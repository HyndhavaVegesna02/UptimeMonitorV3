"""Tests for the live composition entrypoint (STORY-016 T5, dossier §17)."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fakes import FakeClock
from src.adapters.outbound.statuspage import StatuspagePublisher
from src.composition.config import AppConfig, ComponentConfig, Config, MonitorConfig
from src.composition.publish_helper import (
    BestEffortPublisher,
    RecordingPublisher,
    StatusWritebackPublisher,
)
from src.composition.run import build_live_loop, main

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.composition.sample_mode import SampleModeIngest
from src.composition.settings import (
    LiveSecrets,
    MissingLiveSecretError,
    Settings,
    load_live_secrets,
)
from src.core.services.decide import DecideService
from src.core.services.ingest_service import IngestService
from src.core.services.pipeline import AntiFlapThresholds


def test_build_live_loop_assembly():
    """build_live_loop assembles the REAL publisher chain (via the shared
    STORY-045 `build_publisher`) + threads orchestration (T5, STORY-045 D2).

    Builds genuine objects (only ``run_periodic`` is patched, to avoid creating
    live coroutines) and asserts the actual nesting + the orchestration extras
    on each ``run_periodic`` call. Constructing the real publishers is what makes
    this test able to catch a mis-wired constructor kwarg — the earlier version
    stubbed every ``__init__`` to a no-op and so green-lit a broken assembly.
    """
    settings = Settings(config_dir="config")
    secrets = LiveSecrets(
        dynatrace_env_url="https://dt.example.com",
        dynatrace_api_token="token-dt",
        statuspage_page_id="page-sp",
        statuspage_api_token="token-sp",
    )
    # Config with 2 signals
    config = Config(
        [
            AppConfig(
                id="app-1",
                name="App 1",
                monitor_provider="dynatrace",
                components=[
                    ComponentConfig(
                        id="comp-1",
                        name="Comp 1",
                        statuspage_component_id="sp-1",
                        monitors=[
                            MonitorConfig(
                                signal_key="sig-1",
                                native_id="N-1",
                                name="Sig 1",
                                interval_seconds=30,
                            ),
                            MonitorConfig(
                                signal_key="sig-2",
                                native_id="N-2",
                                name="Sig 2",
                                interval_seconds=60,
                            ),
                        ],
                    )
                ],
                thresholds=AntiFlapThresholds(
                    major=3, partial=2, degraded=1, recovery=1
                ),
            )
        ]
    )

    db_resource = MagicMock()
    clock = FakeClock(datetime(2026, 6, 29, 0, 0, tzinfo=timezone.utc))

    # Only run_periodic is patched — every publisher / service / repo is real,
    # so the real constructors run and the nesting below is genuinely exercised.
    async def dummy_coro():
        pass

    with patch("src.composition.run.run_periodic") as mock_run_periodic:
        mock_run_periodic.side_effect = lambda *args, **kwargs: dummy_coro()
        loops = build_live_loop(
            settings=settings,
            secrets=secrets,
            config=config,
            db_resource=db_resource,
            clock=clock,
        )

    for coro in loops:
        coro.close()

    # One run_periodic per signal (2 signals)
    assert len(loops) == 2
    assert mock_run_periodic.call_count == 2

    # Every call carries the six orchestration extras (so the loop actually
    # orchestrates after ingest — not the ingest-only fall-through path).
    for call in mock_run_periodic.call_args_list:
        for extra in (
            "config",
            "observation_repo",
            "maintenance_repo",
            "component_repo",
            "decide_service",
            "clock",
        ):
            assert extra in call.kwargs, f"run_periodic missing extra {extra!r}"
        assert call.kwargs["clock"] is clock
        assert call.kwargs["config"] is config

    # STORY-048 (D4, AC3/AC4, sanctioned AC7b exception): ingest_port is now
    # a SampleModeIngest wrapping the REAL IngestService wired to the real
    # repos — asserts the actual nesting, not a stubbed constructor.
    ingest_port = mock_run_periodic.call_args_list[0].kwargs["ingest_port"]
    assert isinstance(ingest_port, SampleModeIngest)
    assert isinstance(ingest_port._delegate, IngestService)
    assert ingest_port._delegate._observation_repo is not None
    assert ingest_port._delegate._watermark_repo is not None
    assert ingest_port._delegate._rejected_repo is not None
    assert ingest_port._delegate._clock is clock
    from src.adapters.persistence.dynamo_sample_mode_repository import (
        DynamoSampleModeRepository,
    )

    assert isinstance(ingest_port._sample_mode_repo, DynamoSampleModeRepository)
    # Same ingest_port instance threads into every per-signal run_periodic call.
    for call in mock_run_periodic.call_args_list:
        assert call.kwargs["ingest_port"] is ingest_port

    # The publisher chain reaches DecideService correctly nested (STORY-045 D2):
    # DecideService(publisher=StatusWritebackPublisher(BestEffortPublisher(
    #     RecordingPublisher(StatuspagePublisher)), component_repo))
    decide_service = mock_run_periodic.call_args_list[0].kwargs["decide_service"]
    assert isinstance(decide_service, DecideService)
    writeback = decide_service._publisher
    assert isinstance(writeback, StatusWritebackPublisher)
    assert (
        writeback._component_repo
        is mock_run_periodic.call_args_list[0].kwargs["component_repo"]
    )
    best_effort = writeback._delegate
    assert isinstance(best_effort, BestEffortPublisher)
    recording = best_effort._delegate
    assert isinstance(recording, RecordingPublisher)
    statuspage = recording._delegate
    assert isinstance(statuspage, StatuspagePublisher)

    # StatuspagePublisher built from the secrets + the config-derived mapping.
    assert statuspage._page_id == "page-sp"
    assert statuspage._api_token == "token-sp"
    assert statuspage._component_mapping == {"comp-1": "sp-1"}

    # Per-signal identity threaded through (one loop per configured signal).
    signal_keys = {
        call.kwargs["signal_key"] for call in mock_run_periodic.call_args_list
    }
    assert signal_keys == {"sig-1", "sig-2"}


def test_build_live_loop_assembly_statuspage_absent():
    """Verify that when Statuspage secrets are absent, build_live_loop wires LoggingPublisher directly (AC5)."""
    settings = Settings(config_dir="config")
    # Statuspage secrets are None
    secrets = LiveSecrets(
        dynatrace_env_url="https://dt.example.com",
        dynatrace_api_token="token-dt",
        statuspage_page_id=None,
        statuspage_api_token=None,
    )
    config = Config(
        [
            AppConfig(
                id="app-1",
                name="App 1",
                monitor_provider="dynatrace",
                components=[
                    ComponentConfig(
                        id="comp-1",
                        name="Comp 1",
                        statuspage_component_id="sp-1",
                        monitors=[
                            MonitorConfig(
                                signal_key="sig-1",
                                native_id="N-1",
                                name="Sig 1",
                                interval_seconds=30,
                            )
                        ],
                    )
                ],
                thresholds=AntiFlapThresholds(
                    major=3, partial=2, degraded=1, recovery=1
                ),
            )
        ]
    )

    db_resource = MagicMock()
    clock = FakeClock(datetime(2026, 6, 29, 0, 0, tzinfo=timezone.utc))

    from src.composition.publish_helper import LoggingPublisher

    async def dummy_coro():
        pass

    with patch("src.composition.run.run_periodic") as mock_run_periodic:
        mock_run_periodic.side_effect = lambda *args, **kwargs: dummy_coro()
        loops = build_live_loop(
            settings=settings,
            secrets=secrets,
            config=config,
            db_resource=db_resource,
            clock=clock,
        )

    for coro in loops:
        coro.close()

    decide_service = mock_run_periodic.call_args_list[0].kwargs["decide_service"]
    assert isinstance(decide_service, DecideService)
    # STORY-045 D2: write-back still applies on the no-creds local dev path.
    writeback = decide_service._publisher
    assert isinstance(writeback, StatusWritebackPublisher)
    assert isinstance(writeback._delegate, LoggingPublisher)


@patch("src.composition.run.load_dotenv")
@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.load_config")
@patch("src.composition.run.make_dynamo_resource")
@patch("src.composition.run.seed_topology_dynamo")
@patch("src.composition.run.build_live_loop")
def test_main_resource_lifecycle_success(
    mock_build_loop,
    mock_seed_topology_dynamo,
    mock_make_dynamo_resource,
    mock_load_config,
    mock_load_secrets,
    mock_load_settings,
    mock_load_dotenv,
):
    """Verify that main() runs on successful startup/execution."""
    mock_db_resource = MagicMock()
    mock_make_dynamo_resource.return_value = mock_db_resource

    mock_load_settings.return_value = Settings(config_dir="dir")
    mock_load_secrets.return_value = LiveSecrets("dt", "dt-token", "sp", "sp-token")
    mock_load_config.return_value = Config([])

    mock_build_loop.return_value = []  # No loops, exits quickly

    asyncio.run(main())

    # STORY-093 AC3: real assertions on the resource-lifecycle surface —
    # the DynamoDB resource is constructed once, the topology is seeded
    # through it with the real call shape (config, resource, control table
    # name — run.py:202), and the loops are built.
    mock_make_dynamo_resource.assert_called_once()
    mock_seed_topology_dynamo.assert_called_once_with(
        mock_load_config.return_value, mock_db_resource, "uptime-control"
    )
    mock_build_loop.assert_called_once()


@patch("src.composition.run.load_dotenv")
@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.load_config")
@patch("src.composition.run.make_dynamo_resource")
@patch("src.composition.run.seed_topology_dynamo")
def test_main_resource_lifecycle_failure_during_seeding(
    mock_seed_topology_dynamo,
    mock_make_dynamo_resource,
    mock_load_config,
    mock_load_secrets,
    mock_load_settings,
    mock_load_dotenv,
):
    """Verify that main() fails if topology seeding fails."""
    mock_db_resource = MagicMock()
    mock_make_dynamo_resource.return_value = mock_db_resource

    mock_load_settings.return_value = Settings(config_dir="dir")
    mock_load_secrets.return_value = LiveSecrets("dt", "dt-token", "sp", "sp-token")
    mock_load_config.return_value = Config([])

    # Simulate seeding failure
    mock_seed_topology_dynamo.side_effect = RuntimeError("Seeding failed")

    with pytest.raises(RuntimeError, match="Seeding failed"):
        asyncio.run(main())


@patch("src.composition.run.load_dotenv")
@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.make_dynamo_resource")
@patch("src.composition.run.seed_topology_dynamo")
@patch("src.composition.run.build_live_loop")
def test_main_fails_fast_on_missing_secrets_before_any_loop_starts(
    mock_build_loop,
    mock_seed_topology_dynamo,
    mock_make_dynamo_resource,
    mock_load_secrets,
    mock_load_settings,
    mock_load_dotenv,
):
    """AC2 (STORY-050): startup failures stay fail-fast. `load_live_secrets()`
    runs BEFORE the dynamo resource is created, before topology seeding, and before
    `build_live_loop`/`run_periodic` ever exist -- so a `MissingLiveSecretError`
    there must terminate the process untouched by STORY-050's per-cycle
    resilience.
    """
    mock_load_settings.return_value = Settings(config_dir="dir")
    mock_load_secrets.side_effect = MissingLiveSecretError(
        "Missing required secrets: DYNATRACE_ENV_URL, DYNATRACE_API_TOKEN"
    )

    with pytest.raises(MissingLiveSecretError):
        asyncio.run(main())

    # Nothing past secret loading ever ran.
    mock_make_dynamo_resource.assert_not_called()
    mock_seed_topology_dynamo.assert_not_called()
    mock_build_loop.assert_not_called()


@patch("src.composition.run.load_dotenv")
@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.load_config")
@patch("src.composition.run.make_dynamo_resource")
@patch("src.composition.run.seed_topology_dynamo")
@patch("src.composition.run.build_live_loop")
def test_main_calls_load_dotenv_before_settings_and_secrets(
    mock_build_loop,
    mock_seed_topology_dynamo,
    mock_make_dynamo_resource,
    mock_load_config,
    mock_load_secrets,
    mock_load_settings,
    mock_load_dotenv,
):
    """AC1/AC2/AC4 (STORY-043): `main()` loads `.env` at the process
    entrypoint, BEFORE `load_settings()`/`load_live_secrets()` read the
    environment.
    """
    manager = MagicMock()
    manager.attach_mock(mock_load_dotenv, "load_dotenv")
    manager.attach_mock(mock_load_settings, "load_settings")
    manager.attach_mock(mock_load_secrets, "load_live_secrets")

    mock_load_settings.return_value = Settings(config_dir="dir")
    mock_load_secrets.return_value = LiveSecrets("dt", "dt-token", "sp", "sp-token")
    mock_load_config.return_value = Config([])
    mock_build_loop.return_value = []

    asyncio.run(main())

    mock_load_dotenv.assert_called_once_with()
    call_names = [call[0] for call in manager.mock_calls]
    assert call_names.index("load_dotenv") < call_names.index("load_settings")
    assert call_names.index("load_settings") < call_names.index("load_live_secrets")


@patch("src.composition.run.load_dotenv")
@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.load_config")
@patch("src.composition.run.make_dynamo_resource")
@patch("src.composition.run.seed_topology_dynamo")
@patch("src.composition.run.build_live_loop")
@patch("src.composition.run.check_vendor_id_health")
def test_main_probes_vendor_id_health_before_loops_start(
    mock_check_vendor_id_health,
    mock_build_loop,
    mock_seed_topology_dynamo,
    mock_make_dynamo_resource,
    mock_load_config,
    mock_load_secrets,
    mock_load_settings,
    mock_load_dotenv,
):
    """STORY-070: `main()` runs the vendor-id drift health probe at startup,
    passing it the loaded `config` and a real Grail executor -- BEFORE the loops are built.
    """
    mock_db_resource = MagicMock()
    mock_make_dynamo_resource.return_value = mock_db_resource

    mock_load_settings.return_value = Settings(config_dir="dir")
    mock_load_secrets.return_value = LiveSecrets("dt", "dt-token", "sp", "sp-token")
    the_config = Config([])
    mock_load_config.return_value = the_config

    mock_build_loop.return_value = []

    manager = MagicMock()
    manager.attach_mock(mock_check_vendor_id_health, "check_vendor_id_health")
    manager.attach_mock(mock_build_loop, "build_live_loop")

    asyncio.run(main())

    mock_check_vendor_id_health.assert_called_once()
    _, kwargs = mock_check_vendor_id_health.call_args
    assert kwargs["config"] is the_config
    assert callable(kwargs["executor"])

    # Runs before the loops are assembled/started.
    call_names = [call[0] for call in manager.mock_calls]
    assert call_names.index("check_vendor_id_health") < call_names.index(
        "build_live_loop"
    )


def test_dotenv_loading_resolves_live_secrets_not_previously_exported(
    tmp_path, monkeypatch
):
    """AC1: the mechanism the entrypoints use -- `dotenv.load_dotenv` loading a
    `.env` file into `os.environ` -- is sufficient for `load_live_secrets()` to
    resolve secrets that were NEVER exported into the shell, only present in a
    temp `.env` file. Uses an explicit `dotenv_path` (never the bare no-arg
    call the entrypoints use) so this test is deterministic and NEVER touches
    the real repo-root `.env` (credential safety — fake values only).
    """
    for var in (
        "DYNATRACE_ENV_URL",
        "DYNATRACE_API_TOKEN",
        "STATUSPAGE_PAGE_ID",
        "STATUSPAGE_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "DYNATRACE_ENV_URL=https://fake-tenant.example.com\n"
        "DYNATRACE_API_TOKEN=fake-token-123\n",
        encoding="utf-8",
    )

    assert "DYNATRACE_ENV_URL" not in os.environ

    from dotenv import load_dotenv as real_load_dotenv

    real_load_dotenv(dotenv_path=env_file)

    secrets = load_live_secrets()
    assert secrets.dynatrace_env_url == "https://fake-tenant.example.com"
    assert secrets.dynatrace_api_token == "fake-token-123"


def test_dotenv_loading_does_not_override_exported_env_var(tmp_path, monkeypatch):
    """AC3: an already-exported env var wins over the `.env` file's value
    (`load_dotenv`'s default `override=False` semantics) -- production
    (Railway), which sets real env vars and has no `.env` file, is unaffected
    by this mechanism; and a developer's exported override always wins.
    """
    monkeypatch.setenv("DYNATRACE_ENV_URL", "https://exported.example.com")
    monkeypatch.delenv("DYNATRACE_API_TOKEN", raising=False)

    env_file = tmp_path / ".env"
    env_file.write_text(
        "DYNATRACE_ENV_URL=https://from-dotenv.example.com\n"
        "DYNATRACE_API_TOKEN=fake-token-123\n",
        encoding="utf-8",
    )

    from dotenv import load_dotenv as real_load_dotenv

    real_load_dotenv(dotenv_path=env_file)

    secrets = load_live_secrets()
    # The exported var is NOT overridden by .env.
    assert secrets.dynatrace_env_url == "https://exported.example.com"
    # A var absent from the shell still resolves from .env.
    assert secrets.dynatrace_api_token == "fake-token-123"
