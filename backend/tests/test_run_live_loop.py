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
from src.composition.publish_helper import BestEffortPublisher, RecordingPublisher
from src.composition.run import build_live_loop, main
from src.composition.settings import LiveSecrets, Settings
from src.core.services.decide import DecideService
from src.core.services.pipeline import AntiFlapThresholds


def test_build_live_loop_assembly():
    """build_live_loop assembles the REAL publisher chain + threads orchestration (T5).

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
    with patch("src.composition.run.run_periodic") as mock_run_periodic:
        loops = build_live_loop(
            settings=settings,
            secrets=secrets,
            config=config,
            engine=engine,
            clock=clock,
        )

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

    # The publisher chain reaches DecideService correctly nested:
    # DecideService(publisher=BestEffortPublisher(RecordingPublisher(StatuspagePublisher)))
    decide_service = mock_run_periodic.call_args_list[0].kwargs["decide_service"]
    assert isinstance(decide_service, DecideService)
    best_effort = decide_service._publisher
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
