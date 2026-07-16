"""STORY-016a (Phase D1): integration test for orchestrate_signal using DynamoDB Local."""

from __future__ import annotations

from datetime import datetime, timezone

from fakes import RecordingStatusPublisher
from src.adapters.persistence.dynamo_component_repository import (
    DynamoComponentRepository,
)
from src.adapters.persistence.dynamo_maintenance_repository import (
    DynamoMaintenanceRepository,
)
from src.adapters.persistence.dynamo_observation_repository import (
    DynamoObservationRepository,
)
from src.adapters.persistence.dynamo_proposal_repository import DynamoProposalRepository
from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.orchestrate import orchestrate_signal
from src.composition.seed_dynamo import seed_topology_dynamo
from src.composition.settings import load_settings
from src.core.domain import ComponentStatus, Health, Provenance, SignalObservation
from src.core.domain.proposal import ProposalState
from src.core.services.decide import DecideAction, DecideService
from src.core.services.pipeline import AntiFlapThresholds


class FakeClock:
    def __init__(self, now_time: datetime) -> None:
        self._now = now_time

    def now(self) -> datetime:
        return self._now


def test_orchestrate_signal_db_integration(
    dynamo_local, dynamo_resource, clean_dynamo_tables
):
    """Phase D1: run orchestrate_signal against real DynamoDB repository adapters.

    Asserts that a real status_proposals row is opened in DynamoDB when major threshold is met.
    """
    settings = load_settings()

    app_id = "sockshop-int"
    component_id = "checkout-int"
    signal_key = "checkout-http-int"

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

    # Seed the DynamoDB structure
    seed_topology_dynamo(config, dynamo_resource, settings.dynamo_control_table)

    # Initialize real repositories
    observation_repo = DynamoObservationRepository(
        dynamo_resource, settings.dynamo_observations_table
    )
    component_repo = DynamoComponentRepository(
        dynamo_resource, settings.dynamo_control_table
    )
    maintenance_repo = DynamoMaintenanceRepository(
        dynamo_resource, settings.dynamo_control_table
    )
    proposal_repo = DynamoProposalRepository(
        dynamo_resource, settings.dynamo_control_table
    )

    # Now let's place 3 DOWN observations at 1-min interval
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

    observation_repo.save_new([obs1, obs2, obs3])

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
