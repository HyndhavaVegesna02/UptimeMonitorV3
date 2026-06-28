"""STORY-016a (Phase D1): throwaway-DB integration test for orchestrate_signal.

Seeds observations + app + component + signal into a real migrated throwaway
Postgres DB, runs orchestrate_signal against Postgres-backed repository adapters
reconciled via DecideService, and asserts a real status_proposals row is opened.
"""

import json
from datetime import datetime, timezone

import psycopg
from fakes import RecordingStatusPublisher
from src.adapters.persistence.component_repository import PostgresComponentRepository
from src.adapters.persistence.maintenance_repository import (
    PostgresMaintenanceRepository,
)
from src.adapters.persistence.observation_repository import (
    PostgresObservationRepository,
)
from src.adapters.persistence.proposal_repository import PostgresProposalRepository
from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.orchestrate import orchestrate_signal
from src.core.domain import ComponentStatus, Health, Provenance, SignalObservation
from src.core.domain.proposal import ProposalState
from src.core.services.decide import DecideAction, DecideService
from src.core.services.pipeline import AntiFlapThresholds


class FakeClock:
    def __init__(self, now_time: datetime) -> None:
        self._now = now_time

    def now(self) -> datetime:
        return self._now


def seed_db_topology(
    database_url: str, app_id: str, component_id: str, signal_key: str
) -> None:
    """Helper to seed app, component, and signal topology into the database."""
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Seed App
            cur.execute(
                """
                INSERT INTO apps (id, name, config)
                VALUES (%s, %s, '{}'::jsonb)
                ON CONFLICT (id) DO NOTHING
                """,
                (app_id, app_id),
            )
            # Seed Component
            cur.execute(
                """
                INSERT INTO components (id, app_id, name, status)
                VALUES (%s, %s, %s, 'operational')
                ON CONFLICT (id) DO NOTHING
                """,
                (component_id, app_id, component_id),
            )
            # Seed Signal
            cur.execute(
                """
                INSERT INTO signals (signal_key, app_id, name)
                VALUES (%s, %s, %s)
                ON CONFLICT (signal_key) DO NOTHING
                """,
                (signal_key, app_id, signal_key),
            )
        conn.commit()


def seed_db_observation(database_url: str, obs: SignalObservation) -> None:
    """Helper to insert an observation directly into the database."""
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO observations (signal_key, observed_at, health, source_event_id, source, location)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    obs.signal_key,
                    obs.observed_at,
                    obs.health.value,
                    obs.source_event_id,
                    json.dumps(obs.source.model_dump()),
                    obs.location,
                ),
            )
        conn.commit()


def test_orchestrate_signal_db_integration(migrated_db, engine, clean_runtime_tables):
    """Phase D1: run orchestrate_signal against real Postgres repository adapters.

    Asserts that a real status_proposals row is opened in Postgres when major threshold is met.
    """
    app_id = "sockshop-int"
    component_id = "checkout-int"
    signal_key = "checkout-http-int"

    # Seed the DB structure
    seed_db_topology(migrated_db.database_url, app_id, component_id, signal_key)

    # Build memory Config
    thresholds = AntiFlapThresholds(major=3, partial=2, degraded=2, recovery=2)
    sig_cfg = SignalConfig(
        signal_key=signal_key,
        native_id="SYNTHETIC_TEST-ABC",
        name="Checkout HTTP",
        component_id=component_id,
        interval_seconds=60,
    )
    comp_cfg = ComponentConfig(id=component_id, name="Checkout")
    app_cfg = AppConfig(
        id=app_id,
        name="Sock Shop",
        monitor_provider="dynatrace",
        components=[comp_cfg],
        signals=[sig_cfg],
        thresholds=thresholds,
    )
    config = Config([app_cfg])

    # Now let's place 3 DOWN observations at 1-min interval
    # Cycle bounds: major=3, so we check last 5 cycles
    now_ts = datetime(2026, 6, 28, 10, 4, 0, tzinfo=timezone.utc)

    obs1 = SignalObservation(
        signal_key=signal_key,
        observed_at=datetime(2026, 6, 28, 10, 1, 30, tzinfo=timezone.utc),
        health=Health.DOWN,
        source_event_id="evt-int-1",
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east-1",
    )
    obs2 = SignalObservation(
        signal_key=signal_key,
        observed_at=datetime(2026, 6, 28, 10, 2, 30, tzinfo=timezone.utc),
        health=Health.DOWN,
        source_event_id="evt-int-2",
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east-1",
    )
    obs3 = SignalObservation(
        signal_key=signal_key,
        observed_at=datetime(2026, 6, 28, 10, 3, 30, tzinfo=timezone.utc),
        health=Health.DOWN,
        source_event_id="evt-int-3",
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east-1",
    )

    seed_db_observation(migrated_db.database_url, obs1)
    seed_db_observation(migrated_db.database_url, obs2)
    seed_db_observation(migrated_db.database_url, obs3)

    # Initialize real repositories using SQLAlchemy engine
    observation_repo = PostgresObservationRepository(engine)
    component_repo = PostgresComponentRepository(engine)
    maintenance_repo = PostgresMaintenanceRepository(engine)
    proposal_repo = PostgresProposalRepository(engine)

    publisher = RecordingStatusPublisher()
    decide_service = DecideService(proposal_repo=proposal_repo, publisher=publisher)
    clock = FakeClock(now_ts)

    # Run the orchestrator
    action = orchestrate_signal(
        signal_key=signal_key,
        config=config,
        observation_repo=observation_repo,
        maintenance_repo=maintenance_repo,
        component_repo=component_repo,
        decide_service=decide_service,
        clock=clock,
    )

    # The action should be PROPOSED because 3 DOWN observations meet major=3 threshold
    assert action == DecideAction.PROPOSED

    # Assert that a real status_proposals row exists in the database
    open_proposals = proposal_repo.list_open()
    assert len(open_proposals) == 1
    assert open_proposals[0].component_id == component_id
    assert open_proposals[0].to_status == ComponentStatus.MAJOR_OUTAGE
    assert open_proposals[0].state == ProposalState.OPEN
