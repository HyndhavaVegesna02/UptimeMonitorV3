"""Approval service for status proposals (dossier §12, §14 T1.1).

Cites dossier §12 (proposal lifecycle) and §T1.1 (commit-first / best-effort side effects).
"""

from __future__ import annotations

from src.core.domain.proposal import (
    ProposalNotFoundError,
    ProposalNotOpenError,
    ProposalState,
    StatusProposal,
    is_valid_transition,
)
from src.core.domain.status import StatusChange
from src.core.ports import ClockPort, ProposalRepository, StatusPublisherPort

# Re-exported for callers that import the proposal errors from this service
# (the domain owns them; see src.core.domain.proposal).
__all__ = [
    "ApprovalService",
    "ProposalNotFoundError",
    "ProposalNotOpenError",
]


class ApprovalService:
    """Handles manual approvals and rejections of status proposals (dossier §12).

    `publisher` is a REQUIRED keyword-only dependency (STORY-045, D4): a
    silently-unwired publisher is the exact defect this story closes (approving
    a proposal used to be a dead end — see STORY-045's story file), so there is
    deliberately no default. The composition root's `build_publisher` chain
    (`composition/publish_helper.py`) supplies the write-back + best-effort
    Statuspage semantics; this service just publishes — same division of
    responsibility as `core/services/decide.py::DecideService`.
    """

    def __init__(
        self,
        *,
        proposal_repo: ProposalRepository,
        clock: ClockPort,
        publisher: StatusPublisherPort,
    ) -> None:
        self._proposal_repo = proposal_repo
        self._clock = clock
        self._publisher = publisher

    def approve(
        self, proposal_id: int, actor: str, notes: str | None = None
    ) -> StatusProposal:
        """Approve an open status proposal and publish the approved status (dossier §12, STORY-045 AC1).

        Following dossier §T1.1 (commit-first / best-effort side effects), this service
        commits the database resolution BEFORE publishing: `self._publisher.publish(...)`
        is called only after `_decide` has resolved the proposal and recorded the approval
        event, so a publish failure never loses the already-committed decision.
        """
        updated = self._decide(
            proposal_id=proposal_id,
            to_state=ProposalState.APPROVED,
            actor=actor,
            notes=notes,
        )
        change = StatusChange(
            component_id=updated.component_id, status=updated.to_status
        )
        self._publisher.publish(change)
        return updated

    def reject(
        self, proposal_id: int, actor: str, notes: str | None = None
    ) -> StatusProposal:
        """Reject an open status proposal — publishes NOTHING (dossier §12, STORY-045 AC1).

        A rejection never reaches the publisher: only an approved degradation
        (or a recovery, via `DecideService`) publishes.

        Following dossier §T1.1 (commit-first / best-effort side effects), this service
        commits the database resolution before return.
        """
        return self._decide(
            proposal_id=proposal_id,
            to_state=ProposalState.REJECTED,
            actor=actor,
            notes=notes,
        )

    def _decide(
        self,
        proposal_id: int,
        to_state: ProposalState,
        actor: str,
        notes: str | None,
    ) -> StatusProposal:
        """Helper to encapsulate load -> guard -> resolve -> record event sequence (dossier §12).

        The recorded `action` is derived from `to_state.value` (STORY-071) — never
        a separately-hard-coded literal — so it can never drift from the spine's
        `ck_approval_events_action` constraint (`action IN ('approved', 'rejected')`),
        which mirrors `ProposalState`'s terminal values one-for-one.
        """
        proposal = self._proposal_repo.get(proposal_id)
        if proposal is None:
            raise ProposalNotFoundError(f"Proposal {proposal_id} not found.")

        # NOTE: ProposalNotOpenError -> HTTP 409 covers both the up-front open-state
        # guard and a lost-race resolve (concurrent double-submit surfaced by the
        # repository, per the 2026-06-28 TOCTOU agreement).
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
        # Record approval event — action derived from to_state, single source of truth.
        self._proposal_repo.record_approval_event(
            proposal_id,
            actor=actor,
            action=to_state.value,
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
