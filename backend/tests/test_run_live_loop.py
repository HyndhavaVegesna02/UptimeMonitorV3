"""Tests for the live composition entrypoint (STORY-016 T5, dossier §17)."""

from __future__ import annotations

import asyncio
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
from src.core.services.ingest_service import IngestService
from src.core.services.pipeline import AntiFlapThresholds


def test_build_live_loop_assembly():
    """Verify that build_live_loop correctly assembles the publishing and decide chain (T5)."""
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
    from datetime import datetime, timezone

    engine = MagicMock(spec=sa.Engine)
    clock = FakeClock(datetime(2026, 6, 29, 0, 0, tzinfo=timezone.utc))

    # Track constructor calls via mocking
    with (
        patch.object(
            StatuspagePublisher, "__init__", return_value=None
        ) as mock_sp_init,
        patch.object(
            RecordingPublisher, "__init__", return_value=None
        ) as mock_rec_init,
        patch.object(
            BestEffortPublisher, "__init__", return_value=None
        ) as mock_be_init,
        patch.object(DecideService, "__init__", return_value=None) as mock_decide_init,
        patch.object(IngestService, "__init__", return_value=None) as mock_ingest_init,
        patch("src.composition.run.run_periodic") as mock_run_periodic,
    ):

        async def dummy_coro():
            pass

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

        # Verify correct wiring arguments
        # IngestService wiring
        mock_ingest_init.assert_called_once()
        _, ingest_kwargs = mock_ingest_init.call_args
        assert ingest_kwargs["clock"] is clock

        # StatuspagePublisher wiring
        mock_sp_init.assert_called_once()
        _, sp_kwargs = mock_sp_init.call_args
        assert sp_kwargs["page_id"] == "page-sp"
        assert sp_kwargs["api_token"] == "token-sp"
        assert sp_kwargs["component_mapping"] == {"comp-1": "sp-1"}

        # RecordingPublisher wraps StatuspagePublisher
        mock_rec_init.assert_called_once()
        # BestEffortPublisher wraps RecordingPublisher
        mock_be_init.assert_called_once()
        # DecideService wraps BestEffortPublisher
        mock_decide_init.assert_called_once()


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
