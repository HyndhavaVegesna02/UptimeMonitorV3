"""Tests for the live composition entrypoint (STORY-016 T5, dossier §17)."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from fakes import FakeClock
from src.adapters.outbound.statuspage import StatuspagePublisher
from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.publish_helper import (
    BestEffortPublisher,
    RecordingPublisher,
    StatusWritebackPublisher,
)
from src.composition.run import build_live_loop, main

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.composition.sample_mode import SampleModeIngest
from src.composition.settings import LiveSecrets, Settings
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
    settings = Settings(
        database_url="postgresql://user:pass@host/db", config_dir="config"
    )
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
                        id="comp-1", name="Comp 1", statuspage_component_id="sp-1"
                    )
                ],
                signals=[
                    SignalConfig(
                        signal_key="sig-1",
                        native_id="N-1",
                        name="Sig 1",
                        component_id="comp-1",
                        interval_seconds=30,
                    ),
                    SignalConfig(
                        signal_key="sig-2",
                        native_id="N-2",
                        name="Sig 2",
                        component_id="comp-1",
                        interval_seconds=60,
                    ),
                ],
                thresholds=AntiFlapThresholds(
                    major=3, partial=2, degraded=1, recovery=1
                ),
            )
        ]
    )

    engine = MagicMock(spec=sa.Engine)
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
            engine=engine,
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
    from src.adapters.persistence.sample_mode_repository import (
        PostgresSampleModeRepository,
    )

    assert isinstance(ingest_port._sample_mode_repo, PostgresSampleModeRepository)
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
    settings = Settings(
        database_url="postgresql://user:pass@host/db", config_dir="config"
    )
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
                        id="comp-1", name="Comp 1", statuspage_component_id="sp-1"
                    )
                ],
                signals=[
                    SignalConfig(
                        signal_key="sig-1",
                        native_id="N-1",
                        name="Sig 1",
                        component_id="comp-1",
                        interval_seconds=30,
                    )
                ],
                thresholds=AntiFlapThresholds(
                    major=3, partial=2, degraded=1, recovery=1
                ),
            )
        ]
    )

    engine = MagicMock(spec=sa.Engine)
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
            engine=engine,
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


@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.load_config")
@patch("sqlalchemy.create_engine")
@patch("src.composition.run.seed_topology")
@patch("src.composition.run.build_live_loop")
def test_main_resource_lifecycle_success(
    mock_build_loop,
    mock_seed_topology,
    mock_create_engine,
    mock_load_config,
    mock_load_secrets,
    mock_load_settings,
):
    """Verify that main() disposes of the engine on successful startup/execution."""
    mock_engine = MagicMock(spec=sa.Engine)
    mock_create_engine.return_value = mock_engine

    mock_load_settings.return_value = Settings(
        database_url="postgresql://host/db", config_dir="dir"
    )
    mock_load_secrets.return_value = LiveSecrets("dt", "dt-token", "sp", "sp-token")
    mock_load_config.return_value = Config([])

    mock_build_loop.return_value = []  # No loops, exits quickly

    asyncio.run(main())

    mock_engine.dispose.assert_called_once()


@patch("src.composition.run.load_settings")
@patch("src.composition.run.load_live_secrets")
@patch("src.composition.run.load_config")
@patch("sqlalchemy.create_engine")
@patch("src.composition.run.seed_topology")
def test_main_resource_lifecycle_failure_during_seeding(
    mock_seed_topology,
    mock_create_engine,
    mock_load_config,
    mock_load_secrets,
    mock_load_settings,
):
    """Verify that main() disposes of the engine even if topology seeding fails (resource cleanup)."""
    mock_engine = MagicMock(spec=sa.Engine)
    mock_create_engine.return_value = mock_engine

    mock_load_settings.return_value = Settings(
        database_url="postgresql://host/db", config_dir="dir"
    )
    mock_load_secrets.return_value = LiveSecrets("dt", "dt-token", "sp", "sp-token")
    mock_load_config.return_value = Config([])

    # Simulate seeding failure
    mock_seed_topology.side_effect = RuntimeError("Seeding failed")

    with pytest.raises(RuntimeError, match="Seeding failed"):
        asyncio.run(main())

    # Verify dispose was still called
    mock_engine.dispose.assert_called_once()
