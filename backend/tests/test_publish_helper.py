"""Tests for composition/publish_helper.py — BestEffortPublisher + RecordingPublisher
+ StatusWritebackPublisher + build_publisher.

STORY-037 Phase C — AC2. STORY-045 — AC1/AC2/AC3/AC4 (write-back decorator + the
shared publisher-chain assembly used by both composition roots).

Tests cover:
- RecordingPublisher records on successful delegate publish.
- RecordingPublisher records NOTHING and re-raises when delegate raises.
- BestEffortPublisher(RecordingPublisher(raising_delegate)) logs+swallows,
  records nothing (the full composition chain).
- StatusWritebackPublisher writes component_repo.set_status BEFORE delegating,
  survives a best-effort delegate failure, and propagates an unknown-component
  ComponentNotFoundError without ever reaching the delegate.
- build_publisher assembles the D2 chain shapes (creds+mapping present vs absent).
"""

from datetime import datetime, timezone

import pytest
from src.core.domain.component import Component, ComponentNotFoundError
from src.core.domain.status import ComponentStatus, StatusChange
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakePublicationRepository,
    RecordingStatusPublisher,
)


def _utc(hour: int = 12) -> datetime:
    return datetime(2026, 6, 29, hour, 0, 0, tzinfo=timezone.utc)


class RaisingPublisher:
    """A fake publisher that always raises on publish (for AC2 failure path)."""

    def publish(self, change: StatusChange) -> None:
        raise RuntimeError("Statuspage is down")


# --- RecordingPublisher (AC2) ---------------------------------------------------


def test_recording_publisher_records_after_successful_publish():
    """AC2: On a successful delegate publish, a Publication is recorded."""
    from src.composition.publish_helper import RecordingPublisher

    delegate = RecordingStatusPublisher()
    repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))
    change = StatusChange(component_id="checkout", status=ComponentStatus.DEGRADED)

    publisher = RecordingPublisher(delegate, repo, clock)
    publisher.publish(change)

    # Delegate was called
    assert len(delegate.published) == 1
    assert delegate.published[0] == change

    # A publication was recorded
    pubs = repo.list_recent()
    assert len(pubs) == 1
    assert pubs[0].component_id == "checkout"
    assert pubs[0].status == ComponentStatus.DEGRADED
    assert pubs[0].published_at == _utc(12)
    assert pubs[0].id is not None


def test_recording_publisher_records_nothing_when_delegate_raises():
    """AC2: If the delegate raises, nothing is recorded and the error propagates."""
    from src.composition.publish_helper import RecordingPublisher

    delegate = RaisingPublisher()
    repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))
    change = StatusChange(component_id="checkout", status=ComponentStatus.DEGRADED)

    publisher = RecordingPublisher(delegate, repo, clock)

    with pytest.raises(RuntimeError, match="Statuspage is down"):
        publisher.publish(change)

    # Nothing was recorded (the error propagated BEFORE recording)
    assert repo.list_recent() == []


def test_best_effort_publisher_wrapping_recording_publisher_swallows_and_records_nothing():
    """AC2: BestEffortPublisher(RecordingPublisher(raising)) logs+swallows, records nothing."""
    from src.composition.publish_helper import BestEffortPublisher, RecordingPublisher

    delegate = RaisingPublisher()
    repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))
    change = StatusChange(component_id="checkout", status=ComponentStatus.MAJOR_OUTAGE)

    # The full production chain: BestEffortPublisher wrapping RecordingPublisher
    recording = RecordingPublisher(delegate, repo, clock)
    best_effort = BestEffortPublisher(recording)

    # Should NOT raise (BestEffortPublisher swallows)
    best_effort.publish(change)

    # Nothing recorded (delegate raised before record happened)
    assert repo.list_recent() == []


def test_recording_publisher_publish_uses_clock_for_published_at():
    """AC2: published_at comes from clock.now(), not wall time."""
    from src.composition.publish_helper import RecordingPublisher

    frozen_time = _utc(9)
    delegate = RecordingStatusPublisher()
    repo = FakePublicationRepository()
    clock = FakeClock(frozen_time)
    change = StatusChange(component_id="login", status=ComponentStatus.OPERATIONAL)

    publisher = RecordingPublisher(delegate, repo, clock)
    publisher.publish(change)

    pubs = repo.list_recent()
    assert pubs[0].published_at == frozen_time


# --- StatusWritebackPublisher (STORY-045, D1) ------------------------------


def _component_repo_with(component_id: str = "checkout") -> FakeComponentRepository:
    comp = Component(
        id=component_id,
        name=component_id,
        status=ComponentStatus.OPERATIONAL,
        app_id="app-1",
    )
    return FakeComponentRepository(components=[comp])


def test_status_writeback_publisher_writes_before_delegating():
    """D1: set_status happens FIRST — observable via a spy delegate that reads
    the repo's status at the moment it is called."""
    from src.composition.publish_helper import StatusWritebackPublisher

    component_repo = _component_repo_with("checkout")
    observed_at_delegate_call = []

    class SpyDelegate:
        def publish(self, change: StatusChange) -> None:
            observed_at_delegate_call.append(
                component_repo.get(change.component_id).status
            )

    publisher = StatusWritebackPublisher(SpyDelegate(), component_repo)
    change = StatusChange(component_id="checkout", status=ComponentStatus.DEGRADED)

    publisher.publish(change)

    assert observed_at_delegate_call == [ComponentStatus.DEGRADED]
    assert component_repo.get("checkout").status == ComponentStatus.DEGRADED


def test_status_writeback_publisher_survives_best_effort_delegate_failure():
    """D1/D2: write-back is OUTSIDE BestEffortPublisher — a delegate failure
    (swallowed by BestEffortPublisher) does not undo the already-done write-back,
    and (per RecordingPublisher semantics) nothing is recorded in publications."""
    from src.composition.publish_helper import (
        BestEffortPublisher,
        RecordingPublisher,
        StatusWritebackPublisher,
    )

    component_repo = _component_repo_with("checkout")
    publication_repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))

    recording = RecordingPublisher(RaisingPublisher(), publication_repo, clock)
    best_effort = BestEffortPublisher(recording)
    writeback = StatusWritebackPublisher(best_effort, component_repo)

    change = StatusChange(component_id="checkout", status=ComponentStatus.MAJOR_OUTAGE)

    # Must NOT raise — BestEffortPublisher swallows the delegate's failure.
    writeback.publish(change)

    assert component_repo.get("checkout").status == ComponentStatus.MAJOR_OUTAGE
    assert publication_repo.list_recent() == []


def test_status_writeback_publisher_unknown_component_propagates():
    """D1: an unknown component id means topology and the change disagree —
    ComponentNotFoundError propagates and the delegate is never reached."""
    from src.composition.publish_helper import StatusWritebackPublisher

    component_repo = FakeComponentRepository()  # empty — no components seeded
    delegate = RecordingStatusPublisher()
    publisher = StatusWritebackPublisher(delegate, component_repo)

    change = StatusChange(component_id="ghost", status=ComponentStatus.DEGRADED)

    with pytest.raises(ComponentNotFoundError):
        publisher.publish(change)

    assert delegate.published == []


# --- build_publisher (STORY-045, D2 shared assembly) -----------------------


def test_build_publisher_creds_and_mapping_present_assembles_full_chain():
    """D2: creds + mapping present -> StatusWritebackPublisher(BestEffortPublisher(
    RecordingPublisher(StatuspagePublisher)), component_repo)."""
    from src.adapters.outbound.statuspage import StatuspagePublisher
    from src.composition.publish_helper import (
        BestEffortPublisher,
        RecordingPublisher,
        StatusWritebackPublisher,
        build_publisher,
    )

    component_repo = _component_repo_with("checkout")
    publication_repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))

    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id="page-1",
        statuspage_api_token="token-1",
        component_mapping={"checkout": "sp-checkout"},
    )

    assert isinstance(publisher, StatusWritebackPublisher)
    assert publisher._component_repo is component_repo

    best_effort = publisher._delegate
    assert isinstance(best_effort, BestEffortPublisher)

    recording = best_effort._delegate
    assert isinstance(recording, RecordingPublisher)
    assert recording._publication_repo is publication_repo
    assert recording._clock is clock

    statuspage = recording._delegate
    assert isinstance(statuspage, StatuspagePublisher)
    assert statuspage._page_id == "page-1"
    assert statuspage._api_token == "token-1"
    assert statuspage._component_mapping == {"checkout": "sp-checkout"}


def test_build_publisher_creds_absent_falls_back_to_logging():
    """D2: missing creds/mapping -> StatusWritebackPublisher(LoggingPublisher(),
    component_repo) — write-back still applies on the no-creds local dev path."""
    from src.composition.publish_helper import (
        LoggingPublisher,
        StatusWritebackPublisher,
        build_publisher,
    )

    component_repo = _component_repo_with("checkout")
    publication_repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))

    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id=None,
        statuspage_api_token=None,
        component_mapping={},
    )

    assert isinstance(publisher, StatusWritebackPublisher)
    assert publisher._component_repo is component_repo
    assert isinstance(publisher._delegate, LoggingPublisher)


def test_build_publisher_mapping_empty_with_creds_falls_back_to_logging():
    """D2: creds present but an empty component_mapping still falls back —
    mirrors composition/run.py's existing three-way AND condition."""
    from src.composition.publish_helper import LoggingPublisher, build_publisher

    component_repo = _component_repo_with("checkout")
    publication_repo = FakePublicationRepository()
    clock = FakeClock(_utc(12))

    publisher = build_publisher(
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        statuspage_page_id="page-1",
        statuspage_api_token="token-1",
        component_mapping={},
    )

    assert isinstance(publisher._delegate, LoggingPublisher)
