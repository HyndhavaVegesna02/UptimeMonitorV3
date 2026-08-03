"""The proposal repository port (dossier §12) — persistence for status proposals."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.core.domain.proposal import ProposalState, StatusProposal


class ProposalRepository(ABC):
    """Port interface for storing and managing status proposals and approval events."""

    @abstractmethod
    def create_open(self, proposal: StatusProposal) -> StatusProposal | None:
        """Persist a new open status proposal.

        Must enforce that only one open proposal exists per component_id.
        If an open proposal already exists, this method returns None.
        Otherwise, returns the persisted StatusProposal (which will have an assigned ID).
        """
        raise NotImplementedError

    @abstractmethod
    def get_open(self, component_id: str) -> StatusProposal | None:
        """Retrieve the open status proposal for a component, if any."""
        raise NotImplementedError

    @abstractmethod
    def resolve(
        self,
        proposal_id: int,
        *,
        to_state: ProposalState,
        reason: str | None,
        resolved_at: datetime,
    ) -> None:
        """Move an open status proposal to a terminal state."""
        raise NotImplementedError

    @abstractmethod
    def record_approval_event(
        self,
        proposal_id: int,
        *,
        actor: str,
        action: ProposalState,
        notes: str | None,
        occurred_at: datetime,
    ) -> None:
        """Record an approval or rejection event for a proposal.

        `action` must be `ProposalState.APPROVED` or `ProposalState.REJECTED` —
        those are the only two legal values, because an approval EVENT can only
        ever record an approve or a reject (dossier §12); the other three
        `ProposalState` members (`OPEN`, `SUPERSEDED`, `OBSOLETED`) are never
        legal here even though they are legal `resolve()` targets.
        Enforcing that 2-member subset is the CALLER's responsibility
        (`ApprovalService._decide` raises `InvalidApprovalActionError` for any
        other value before this port method is ever reached) — this method
        assumes the value has already been validated.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, proposal_id: int) -> StatusProposal | None:
        """Return the proposal with this id, or None if none exists."""
        raise NotImplementedError

    @abstractmethod
    def list_open(self) -> list[StatusProposal]:
        """Retrieve all OPEN status proposals from the repository.

        Returns:
            list[StatusProposal]: A list of all open proposals. Returns `[]` if none exist.
        """
        raise NotImplementedError
