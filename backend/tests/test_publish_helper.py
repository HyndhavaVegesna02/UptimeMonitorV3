"""Tests for composition/publish_helper.py — BestEffortPublisher + RecordingPublisher.

STORY-037 Phase C — AC2.

Tests cover:
- RecordingPublisher records on successful delegate publish.
- RecordingPublisher records NOTHING and re-raises when delegate raises.
- BestEffortPublisher(RecordingPublisher(raising_delegate)) logs+swallows,
  records nothing (the full composition chain).
"""

from datetime import datetime, timezone

import pytest

from src.core.domain.status import ComponentStatus, StatusChange
from tests.fakes import (
    FakeClock,
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
