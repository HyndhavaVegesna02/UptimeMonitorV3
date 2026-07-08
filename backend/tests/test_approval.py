from datetime import datetime, timezone

import pytest
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus, StatusChange
from src.core.services.approval import (
    ApprovalService,
    ProposalNotFoundError,
    ProposalNotOpenError,
)
from tests.fakes import FakeClock, FakeProposalRepository, RecordingStatusPublisher


def _open_proposal(
    component_id: str = "checkout",
    from_status: ComponentStatus = ComponentStatus.OPERATIONAL,
    to_status: ComponentStatus = ComponentStatus.DEGRADED,
) -> StatusProposal:
    return StatusProposal(
        component_id=component_id,
        from_status=from_status,
        to_status=to_status,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )


def test_approval_service_approve_success():
    repo = FakeProposalRepository()
    clock_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(clock_time)
    publisher = RecordingStatusPublisher()

    # Arrange: create an open proposal
    saved = repo.create_open(_open_proposal())
    assert saved is not None

    # Act
    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)
    result = service.approve(
        proposal_id=saved.id, actor="operator-1", notes="Approve this degradation"
    )

    # Assert: returns the resolved proposal
    assert result.state == ProposalState.APPROVED
    assert result.resolved_at == clock_time
    assert result.reason == "Approve this degradation"

    # Assert: resolve was called on repo
    updated_prop = repo.get(saved.id)
    assert updated_prop is not None
    assert updated_prop.state == ProposalState.APPROVED
    assert updated_prop.resolved_at == clock_time
    assert updated_prop.reason == "Approve this degradation"

    # Assert: record_approval_event was called
    assert len(repo.approval_events) == 1
    event = repo.approval_events[0]
    assert event["proposal_id"] == saved.id
    assert event["actor"] == "operator-1"
    assert event["action"] == "approved"
    assert event["notes"] == "Approve this degradation"
    assert event["occurred_at"] == clock_time


def test_approval_service_reject_success():
    repo = FakeProposalRepository()
    clock_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(clock_time)
    publisher = RecordingStatusPublisher()

    saved = repo.create_open(_open_proposal())
    assert saved is not None

    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)
    result = service.reject(
        proposal_id=saved.id, actor="operator-1", notes="Reject this degradation"
    )

    assert result.state == ProposalState.REJECTED
    assert result.resolved_at == clock_time
    assert result.reason == "Reject this degradation"

    updated_prop = repo.get(saved.id)
    assert updated_prop is not None
    assert updated_prop.state == ProposalState.REJECTED

    assert len(repo.approval_events) == 1
    event = repo.approval_events[0]
    assert event["proposal_id"] == saved.id
    assert event["actor"] == "operator-1"
    assert event["action"] == "rejected"
    assert event["notes"] == "Reject this degradation"
    assert event["occurred_at"] == clock_time


def test_approval_service_not_found_raises():
    repo = FakeProposalRepository()
    clock = FakeClock(datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    publisher = RecordingStatusPublisher()
    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)

    with pytest.raises(ProposalNotFoundError):
        service.approve(999, actor="operator-1")

    with pytest.raises(ProposalNotFoundError):
        service.reject(999, actor="operator-1")

    # A guard-path 404 publishes nothing (AC1: only a genuine approve publishes).
    assert publisher.published == []


def test_approval_service_already_terminal_raises():
    repo = FakeProposalRepository()
    clock_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(clock_time)
    publisher = RecordingStatusPublisher()

    saved = repo.create_open(_open_proposal())
    assert saved is not None

    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)
    service.approve(saved.id, actor="operator-1", notes="First resolve")

    # Now it is terminal. Second resolve attempt should raise
    with pytest.raises(ProposalNotOpenError):
        service.approve(saved.id, actor="operator-2", notes="Second resolve")

    with pytest.raises(ProposalNotOpenError):
        service.reject(saved.id, actor="operator-2", notes="Second resolve")

    # Assert that no new events are added (remains exactly 1 event from the first approve)
    assert len(repo.approval_events) == 1

    # Only the first (successful) approve published; the two guard-path
    # re-attempts published nothing more.
    assert len(publisher.published) == 1


# --- STORY-045 AC1/D4: approve publishes, reject does not -----------------


def test_approval_service_approve_publishes_status_change():
    """AC1/D4: approving publishes a StatusChange(component_id, to_status)
    to the injected publisher, AFTER the proposal has been resolved
    (commit-first — the write lands before the publish is observed)."""
    repo = FakeProposalRepository()
    clock = FakeClock(datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    saved = repo.create_open(
        _open_proposal(
            component_id="checkout",
            to_status=ComponentStatus.DEGRADED,
        )
    )
    assert saved is not None

    # A spy publisher that records the proposal's state (via the repo) at the
    # moment publish is called — proves ordering, not just call count.
    observed_state_at_publish = []

    class SpyPublisher:
        def publish(self, change: StatusChange) -> None:
            observed_state_at_publish.append(repo.get(saved.id).state)
            self.received = change

    publisher = SpyPublisher()
    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)

    service.approve(proposal_id=saved.id, actor="operator-1")

    assert observed_state_at_publish == [ProposalState.APPROVED]
    assert publisher.received == StatusChange(
        component_id="checkout", status=ComponentStatus.DEGRADED
    )


def test_approval_service_reject_publishes_nothing():
    """AC1/D4: reject never publishes."""
    repo = FakeProposalRepository()
    clock = FakeClock(datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    publisher = RecordingStatusPublisher()

    saved = repo.create_open(_open_proposal())
    assert saved is not None

    service = ApprovalService(proposal_repo=repo, clock=clock, publisher=publisher)
    service.reject(proposal_id=saved.id, actor="operator-1")

    assert publisher.published == []
