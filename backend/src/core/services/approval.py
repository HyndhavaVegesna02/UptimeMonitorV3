"""Approval service for status proposals (dossier §12, §14 T1.1).

Cites dossier §12 (proposal lifecycle) and §T1.1 (commit-first / best-effort side effects).
"""

from __future__ import annotations

from datetime import datetime

from src.core.domain.proposal import ProposalState, StatusProposal, is_valid_transition
from src.core.ports import ClockPort, ProposalRepository


class ProposalNotFoundError(ValueError):
    """Raised when a proposal cannot be found by its ID."""


class ProposalNotOpenError(ValueError):
    """Raised when a proposal is not in the open state and cannot be resolved."""


class ApprovalService:
    """Handles manual approvals and rejections of status proposals (dossier §12)."""

    def __init__(self, *, proposal_repo: ProposalRepository, clock: ClockPort) -> None:
        self._proposal_repo = proposal_repo
        self._clock = clock

    def approve(
        self, proposal_id: int, actor: str, notes: str | None = None
    ) -> StatusProposal:
        """Approve an open status proposal (dossier §12).

        Following dossier §T1.1 (commit-first / best-effort side effects), this service
        commits the database resolution before return.
        """
        return self._decide(
            proposal_id=proposal_id,
            to_state=ProposalState.APPROVED,
            action="approve",
            actor=actor,
            notes=notes,
        )

    def reject(
        self, proposal_id: int, actor: str, notes: str | None = None
    ) -> StatusProposal:
        """Reject an open status proposal (dossier §12).

        Following dossier §T1.1 (commit-first / best-effort side effects), this service
        commits the database resolution before return.
        """
        return self._decide(
            proposal_id=proposal_id,
            to_state=ProposalState.REJECTED,
            action="reject",
            actor=actor,
            notes=notes,
        )

    def _decide(
        self,
        proposal_id: int,
        to_state: ProposalState,
        action: str,
        actor: str,
        notes: str | None,
    ) -> StatusProposal:
        """Helper to encapsulate load -> guard -> resolve -> record event sequence (dossier §12)."""
        proposal = self._proposal_repo.get(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(f"Proposal {proposal_id} not found.")

        if not is_valid_transition(proposal.state, to_state):
            raise ProposalNotOpenError(
                f"Proposal {proposal_id} is in state {proposal.state.value} and cannot transition to {to_state.value}."
            )

        now = self._clock.now()
        # Resolve the proposal in the repository
        self._proposal_repo.resolve(
            proposal_id,
            to_state=to_state,
            reason=notes,
            resolved_at=now,
        )
        # Record approval event
        self._proposal_repo.record_approval_event(
            proposal_id,
            actor=actor,
            action=action,
            notes=notes,
            occurred_at=now,
        )

        # Retrieve and return the updated proposal
        updated = self._proposal_repo.get(proposal_id)
        if updated is None:
            raise ProposalNotFoundError(
                f"Proposal {proposal_id} disappeared after resolution."
            )
        return updated

