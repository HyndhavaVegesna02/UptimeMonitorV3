"""STORY-005: the core's owned port interfaces (dossier §6, §8).

Zone 1 / pure core. Ports are ABCs the core OWNS but does not implement. Each
test proves two things: the ABC cannot be instantiated directly (it is abstract),
and the in-memory fake under `tests/fakes.py` satisfies the interface and behaves.
No Dynatrace, Statuspage, Neon, DB, or network anywhere here.
"""

from datetime import datetime, timedelta, timezone

import pytest
from src.core.domain import (
    ComponentStatus,
    Health,
    IngestResult,
    Provenance,
    SignalObservation,
    StatusChange,
)
from src.core.ports import (
    ClockPort,
    ObservationRepository,
    SignalIngestPort,
    StatusPublisherPort,
    WatermarkRepository,
)


def _observation(signal_key: str = "checkout-http", event_id: str = "evt-1"):
    """A valid canonical observation for exercising the persistence/ingest fakes."""
    return SignalObservation(
        signal_key=signal_key,
        observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=Health.UP,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east",
    )


# --- ClockPort (AC1, AC3) -------------------------------------------------------


def test_clock_port_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ClockPort()  # type: ignore[abstract]


def test_fake_clock_returns_injected_fixed_tz_aware_utc_time():
    from fakes import FakeClock

    fixed = datetime(2026, 6, 24, 9, 30, 0, tzinfo=timezone.utc)
    clock = FakeClock(fixed)

    now = clock.now()
    assert now == fixed
    assert now.tzinfo is not None  # tz-aware
    assert now.utcoffset() == timedelta(0)  # UTC
    assert clock.now() == fixed  # frozen: stable across calls


# --- WatermarkRepository (AC1, AC4) ---------------------------------------------


def test_watermark_repository_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        WatermarkRepository()  # type: ignore[abstract]


def test_fake_watermark_get_returns_none_when_unset():
    from fakes import FakeWatermarkRepository

    repo = FakeWatermarkRepository()
    assert repo.get("checkout-http") is None


def test_fake_watermark_advance_then_get_round_trips():
    from fakes import FakeWatermarkRepository

    repo = FakeWatermarkRepository()
    mark = datetime(2026, 6, 24, 10, 5, 0, tzinfo=timezone.utc)

    repo.advance("checkout-http", mark)

    assert repo.get("checkout-http") == mark
    # A watermark is per-signal: advancing one leaves others unset.
    assert repo.get("login-http") is None


# --- ObservationRepository (AC1) ------------------------------------------------


def test_observation_repository_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        ObservationRepository()  # type: ignore[abstract]


def test_fake_observation_repository_save_new_returns_insert_count():
    from fakes import FakeObservationRepository

    repo = FakeObservationRepository()
    batch = [_observation(event_id="evt-1"), _observation(event_id="evt-2")]

    inserted = repo.save_new(batch)

    assert inserted == 2
    assert repo.saved == batch


def test_fake_observation_repository_save_new_of_empty_batch_is_zero():
    from fakes import FakeObservationRepository

    repo = FakeObservationRepository()
    assert repo.save_new([]) == 0


def test_fake_observation_repository_in_window_filters_by_signal_and_half_open_range():
    from fakes import FakeObservationRepository

    repo = FakeObservationRepository()
    since = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    until = datetime(2026, 6, 24, 11, 0, 0, tzinfo=timezone.utc)
    in_range = SignalObservation(
        signal_key="checkout-http",
        observed_at=since,
        health=Health.UP,
        source_event_id="evt-in-range",
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east",
    )
    at_until_boundary = SignalObservation(
        signal_key="checkout-http",
        observed_at=until,
        health=Health.UP,
        source_event_id="evt-at-boundary",
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east",
    )
    other_signal = SignalObservation(
        signal_key="login-http",
        observed_at=since,
        health=Health.UP,
        source_event_id="evt-other-signal",
        source=Provenance(system="dynatrace", native_id="X-1", native_kind="http"),
        location="us-east",
    )
    repo.save_new([in_range, at_until_boundary, other_signal])

    result = repo.in_window("checkout-http", since, until)

    assert result == [in_range]


# --- StatusPublisherPort (AC1) --------------------------------------------------


def test_status_publisher_port_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        StatusPublisherPort()  # type: ignore[abstract]


def test_recording_status_publisher_records_each_canonical_change():
    from fakes import RecordingStatusPublisher

    publisher = RecordingStatusPublisher()
    change = StatusChange(component_id="checkout", status=ComponentStatus.MAJOR_OUTAGE)

    result = publisher.publish(change)

    assert result is None  # publish returns None by contract
    assert publisher.published == [change]


# --- SignalIngestPort (AC1) -----------------------------------------------------


def test_signal_ingest_port_is_abstract_and_cannot_be_instantiated():
    with pytest.raises(TypeError):
        SignalIngestPort()  # type: ignore[abstract]


def test_fake_signal_ingest_returns_ingest_result_over_canonical_batch():
    from fakes import FakeSignalIngestPort

    port = FakeSignalIngestPort()
    batch = [_observation(event_id="evt-1"), _observation(event_id="evt-2")]

    result = port.ingest_observations(batch)

    assert isinstance(result, IngestResult)
    assert result.accepted == 2
    assert result.rejected == 0
    assert port.received == batch


# --- ProposalRepository --------------------------------------------------------


def test_proposal_repository_is_abstract_and_cannot_be_instantiated():
    from src.core.ports import ProposalRepository

    with pytest.raises(TypeError):
        ProposalRepository()  # type: ignore[abstract]


def test_fake_proposal_repository_create_and_get():
    from fakes import FakeProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    repo = FakeProposalRepository()
    prop1 = StatusProposal(
        component_id="checkout",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )

    # First open proposal succeeds
    saved = repo.create_open(prop1)
    assert saved is not None
    assert saved.id is not None
    assert saved.component_id == "checkout"

    # Second open proposal for same component returns None (honors one-open-per-component)
    prop2 = StatusProposal(
        component_id="checkout",
        from_status=None,
        to_status=ComponentStatus.MAJOR_OUTAGE,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 1, 0, tzinfo=timezone.utc),
    )
    assert repo.create_open(prop2) is None

    # Get open returns the active open proposal
    open_prop = repo.get_open("checkout")
    assert open_prop is not None
    assert open_prop.id == saved.id
    assert open_prop.state == ProposalState.OPEN

    # Resolve transitions the proposal to a terminal state
    resolved_time = datetime(2026, 6, 26, 12, 10, 0, tzinfo=timezone.utc)
    repo.resolve(
        saved.id,
        to_state=ProposalState.APPROVED,
        reason="Manual approve",
        resolved_at=resolved_time,
    )

    # Now get_open returns None
    assert repo.get_open("checkout") is None

    # And a new open proposal can now be created
    saved2 = repo.create_open(prop2)
    assert saved2 is not None
    assert saved2.id != saved.id

    # Record approval event writes to approval events
    repo.record_approval_event(
        saved.id,
        actor="ops-1",
        action=ProposalState.APPROVED,
        notes="Checked logs, all good",
        occurred_at=resolved_time,
    )
    assert len(repo.approval_events) == 1
    evt = repo.approval_events[0]
    assert evt["proposal_id"] == saved.id
    assert evt["actor"] == "ops-1"
    assert evt["action"] == "approved"
    assert evt["notes"] == "Checked logs, all good"
    assert evt["occurred_at"] == resolved_time


def test_fake_proposal_repository_resolve_non_open_or_unknown_raises():
    from fakes import FakeProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal

    repo = FakeProposalRepository()
    resolved_time = datetime(2026, 6, 26, 12, 10, 0, tzinfo=timezone.utc)

    # Unknown ID raises
    with pytest.raises(ValueError):
        repo.resolve(
            999,
            to_state=ProposalState.APPROVED,
            reason="test",
            resolved_at=resolved_time,
        )

    prop = StatusProposal(
        component_id="checkout",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    # First resolve succeeds
    repo.resolve(
        saved.id,
        to_state=ProposalState.APPROVED,
        reason="first",
        resolved_at=resolved_time,
    )

    # Resolving again (now terminal, not open) raises ValueError
    with pytest.raises(ValueError):
        repo.resolve(
            saved.id,
            to_state=ProposalState.SUPERSEDED,
            reason="second",
            resolved_at=resolved_time,
        )


def test_fake_proposal_repository_get():
    from datetime import timezone

    from fakes import FakeProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal
    from src.core.domain.status import ComponentStatus

    repo = FakeProposalRepository()
    assert repo.get(999) is None

    prop = StatusProposal(
        component_id="checkout",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None
    assert saved.id is not None

    retrieved = repo.get(saved.id)
    assert retrieved is not None
    assert retrieved.id == saved.id
    assert retrieved.component_id == "checkout"


def test_fake_proposal_repository_list_open():
    from datetime import timezone

    from fakes import FakeProposalRepository
    from src.core.domain.proposal import ProposalState, StatusProposal
    from src.core.domain.status import ComponentStatus

    repo = FakeProposalRepository()
    # Empty case returns []
    assert repo.list_open() == []

    prop1 = StatusProposal(
        component_id="checkout",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved1 = repo.create_open(prop1)
    assert saved1 is not None

    # Retrieve when one open proposal exists
    assert repo.list_open() == [saved1]

    # Resolve proposal (move to terminal APPROVED state)
    repo.resolve(
        saved1.id,
        to_state=ProposalState.APPROVED,
        reason="Approved",
        resolved_at=datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc),
    )

    # Empty case again because the proposal is terminal
    assert repo.list_open() == []


def test_component_repository_port_is_abstract():
    from src.core.ports.component_repository import ComponentRepository

    with pytest.raises(TypeError):
        ComponentRepository()  # type: ignore[abstract]


def test_fake_component_repository_list():
    from fakes import FakeComponentRepository
    from src.core.domain.component import Component
    from src.core.domain.status import ComponentStatus

    repo = FakeComponentRepository()
    # Empty case returns []
    assert repo.list_components() == []

    # Injected components case
    comp1 = Component(
        id="c1", name="Comp 1", status=ComponentStatus.OPERATIONAL, app_id="app-1"
    )
    comp2 = Component(
        id="c2", name="Comp 2", status=ComponentStatus.DEGRADED, app_id="app-1"
    )
    repo = FakeComponentRepository(components=[comp1, comp2])
    assert repo.list_components() == [comp1, comp2]


def test_fake_component_repository_get():
    """FakeComponentRepository.get returns the component by id, None when absent.

    Fake/adapter parity contract (working-agreements.md 2026-06-26):
    same None-on-not-found behaviour as PostgresComponentRepository.get (A3).
    """
    from fakes import FakeComponentRepository
    from src.core.domain.component import Component
    from src.core.domain.status import ComponentStatus

    comp = Component(
        id="checkout",
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    repo = FakeComponentRepository(components=[comp])

    # found
    result = repo.get("checkout")
    assert result == comp

    # not found → None, never raises
    assert repo.get("does-not-exist") is None

    # empty repo → None
    empty_repo = FakeComponentRepository()
    assert empty_repo.get("checkout") is None


def test_maintenance_repository_port_is_abstract():
    from src.core.ports.maintenance_repository import MaintenanceRepository

    with pytest.raises(TypeError):
        MaintenanceRepository()  # type: ignore[abstract]


def test_fake_maintenance_repository():
    from datetime import datetime, timezone

    from fakes import FakeMaintenanceRepository
    from src.core.domain.maintenance import MaintenanceWindow

    repo = FakeMaintenanceRepository()
    # Empty case returns []
    assert repo.list_windows() == []
    # Empty case is not under maintenance
    at_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    assert repo.is_under_maintenance("checkout", at_time) is False

    # Create window
    w1 = MaintenanceWindow(
        component_id="checkout",
        starts_at=datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc),
        reason="Update 1",
    )
    saved1 = repo.create(w1)
    assert saved1.id is not None
    assert saved1.component_id == "checkout"
    assert saved1.reason == "Update 1"

    # Create another window, starts earlier so we test ordering
    w2 = MaintenanceWindow(
        component_id="checkout",
        starts_at=datetime(2026, 6, 28, 10, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
        reason="Update 2",
    )
    saved2 = repo.create(w2)
    assert saved2.id is not None

    # list_windows returns all ordered by starts_at
    windows = repo.list_windows()
    assert len(windows) == 2
    assert windows[0].id == saved2.id
    assert windows[1].id == saved1.id

    # Test is_under_maintenance boundaries (inclusive start / exclusive end)
    # 1. Exact start of w1 (inclusive)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
        )
        is True
    )
    # 2. Inside w1
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 13, 0, 0, tzinfo=timezone.utc)
        )
        is True
    )
    # 3. Exact end of w1 (exclusive)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc)
        )
        is False
    )
    # 4. Outside w1 (before)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 11, 30, 0, tzinfo=timezone.utc)
        )
        is False
    )
    # 5. Outside w1 (after)
    assert (
        repo.is_under_maintenance(
            "checkout", datetime(2026, 6, 28, 15, 0, 0, tzinfo=timezone.utc)
        )
        is False
    )

    # Test different component_id
    assert (
        repo.is_under_maintenance(
            "other-component",
            datetime(2026, 6, 28, 12, 30, 0, tzinfo=timezone.utc),
        )
        is False
    )


# --- PublicationRepository (STORY-037, AC1) ------------------------------------


def test_publication_repository_port_is_abstract():
    """B1: PublicationRepository cannot be instantiated directly."""
    from src.core.ports.publication_repository import PublicationRepository

    with pytest.raises(TypeError):
        PublicationRepository()  # type: ignore[abstract]


def test_fake_publication_repository_empty_returns_empty_list():
    """B1: list_recent() returns [] when no publications exist."""
    from fakes import FakePublicationRepository

    repo = FakePublicationRepository()
    assert repo.list_recent() == []


def test_fake_publication_repository_record_returns_publication_with_id():
    """B1: record() returns the Publication with a database-assigned id."""
    from fakes import FakePublicationRepository
    from src.core.domain.publication import Publication
    from src.core.domain.status import ComponentStatus

    repo = FakePublicationRepository()
    pub = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.record(pub)
    assert saved.id is not None
    assert saved.component_id == "checkout"
    assert saved.status == ComponentStatus.OPERATIONAL


def test_fake_publication_repository_list_recent_most_recent_first():
    """B1: list_recent() returns publications ordered most-recent-first."""
    from fakes import FakePublicationRepository
    from src.core.domain.publication import Publication
    from src.core.domain.status import ComponentStatus

    repo = FakePublicationRepository()
    earlier = Publication(
        component_id="checkout",
        status=ComponentStatus.DEGRADED,
        published_at=datetime(2026, 6, 29, 10, 0, 0, tzinfo=timezone.utc),
    )
    later = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=datetime(2026, 6, 29, 12, 0, 0, tzinfo=timezone.utc),
    )
    repo.record(earlier)
    repo.record(later)

    results = repo.list_recent()
    assert len(results) == 2
    assert results[0].published_at > results[1].published_at  # most-recent-first
