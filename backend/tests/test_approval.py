from datetime import datetime, timezone

import pytest
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus
from src.core.services.approval import (
    ApprovalService,
    ProposalNotFoundError,
    ProposalNotOpenError,
)
from tests.fakes import FakeClock, FakeProposalRepository


def test_approval_service_approve_success():
    repo = FakeProposalRepository()
    clock_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(clock_time)

    # Arrange: create an open proposal
    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    # Act
    service = ApprovalService(proposal_repo=repo, clock=clock)
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
    assert event["action"] == "approve"
    assert event["notes"] == "Approve this degradation"
    assert event["occurred_at"] == clock_time


def test_approval_service_reject_success():
    repo = FakeProposalRepository()
    clock_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(clock_time)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    service = ApprovalService(proposal_repo=repo, clock=clock)
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
    assert event["action"] == "reject"
    assert event["notes"] == "Reject this degradation"
    assert event["occurred_at"] == clock_time


def test_approval_service_not_found_raises():
    repo = FakeProposalRepository()
    clock = FakeClock(datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    service = ApprovalService(proposal_repo=repo, clock=clock)

    with pytest.raises(ProposalNotFoundError):
        service.approve(999, actor="operator-1")

    with pytest.raises(ProposalNotFoundError):
        service.reject(999, actor="operator-1")


def test_approval_service_already_terminal_raises():
    repo = FakeProposalRepository()
    clock_time = datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc)
    clock = FakeClock(clock_time)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    service = ApprovalService(proposal_repo=repo, clock=clock)
    service.approve(saved.id, actor="operator-1", notes="First resolve")

    # Now it is terminal. Second resolve attempt should raise
    with pytest.raises(ProposalNotOpenError):
        service.approve(saved.id, actor="operator-2", notes="Second resolve")

    with pytest.raises(ProposalNotOpenError):
        service.reject(saved.id, actor="operator-2", notes="Second resolve")

    # Assert that no new events are added (remains exactly 1 event from the first approve)
    assert len(repo.approval_events) == 1
