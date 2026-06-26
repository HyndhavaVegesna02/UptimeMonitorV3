"""STORY-012: status proposals domain types and state machine (dossier §12)."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from src.core.domain import ComponentStatus
from src.core.domain.proposal import ProposalState, StatusProposal


def test_proposal_state_enum_has_all_states():
    assert {state.value for state in ProposalState} == {
        "open",
        "approved",
        "rejected",
        "superseded",
        "obsoleted",
    }


def test_status_proposal_constructs_valid_open():
    proposal = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        reason="Testing open proposal",
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        resolved_at=None,
        id=42,
    )
    assert proposal.component_id == "checkout"
    assert proposal.from_status == ComponentStatus.OPERATIONAL
    assert proposal.to_status == ComponentStatus.DEGRADED
    assert proposal.state == ProposalState.OPEN
    assert proposal.reason == "Testing open proposal"
    assert proposal.proposed_at == datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc)
    assert proposal.resolved_at is None
    assert proposal.id == 42


def test_status_proposal_constructs_valid_terminal():
    proposal = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.APPROVED,
        reason="Approved by operator",
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        resolved_at=datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc),
        id=42,
    )
    assert proposal.state == ProposalState.APPROVED
    assert proposal.resolved_at == datetime(2026, 6, 26, 12, 5, 0, tzinfo=timezone.utc)


def test_status_proposal_is_frozen():
    proposal = StatusProposal(
        component_id="checkout",
        from_status=None,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        reason=None,
        proposed_at=datetime(2026, 6, 26, 12, 0, 0, tzinfo=timezone.utc),
        resolved_at=None,
    )
    with pytest.raises(ValidationError):
        proposal.component_id = "new-id"
