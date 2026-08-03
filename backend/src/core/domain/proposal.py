"""Status proposal domain models and states (dossier §12)."""

from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from src.core.domain.status import ComponentStatus


class ProposalNotFoundError(ValueError):
    """Raised when a proposal cannot be found by its ID (dossier §12)."""


class ProposalNotOpenError(ValueError):
    """Raised when a proposal is not OPEN and so cannot be resolved (dossier §12).

    The proposal lifecycle only permits resolving an OPEN proposal to a terminal
    state; attempting to resolve a missing or already-terminal proposal (e.g. a
    lost race where a concurrent request resolved it first) raises this.
    """


class InvalidApprovalActionError(ValueError):
    """Raised when an approval-event `action` is outside {APPROVED, REJECTED}
    (dossier §12, STORY-200 AC3).

    `record_approval_event`'s `action` is typed `ProposalState` (the same
    domain type `resolve`'s `to_state` uses), but only two of its five members
    are ever legal to RECORD as an approval event — `is_valid_transition`
    admits any non-OPEN target (e.g. OPEN -> SUPERSEDED), so it does not
    constrain this narrower set. `ApprovalService._decide` raises this before
    ever reaching the repository, so the 2-member contract leaves a testable
    trace instead of living only in a comment.
    """


class ProposalState(str, Enum):
    """Actionable and terminal states for a status proposal (dossier §12)."""

    OPEN = "open"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    OBSOLETED = "obsoleted"


class StatusProposal(BaseModel):
    """A proposal to change a component's status (dossier §12)."""

    model_config = ConfigDict(frozen=True)

    component_id: str
    """Canonical component id owned by the core."""

    from_status: ComponentStatus | None
    """The component's status prior to this proposal (or None if unknown/new)."""

    to_status: ComponentStatus
    """The proposed target status."""

    state: ProposalState
    """Current state of this proposal."""

    reason: str | None = None
    """Reasoning or context for the proposed change/resolution."""

    proposed_at: datetime
    """Timestamp when this proposal was created."""

    resolved_at: datetime | None = None
    """Timestamp when this proposal was resolved (None if still open)."""

    id: int | None = None
    """Optional database ID if persisted."""

    @field_validator("proposed_at")
    @classmethod
    def _require_proposed_at_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC timestamps."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("proposed_at must be a tz-aware UTC datetime")
        return value

    @field_validator("resolved_at")
    @classmethod
    def _require_resolved_at_utc(cls, value: datetime | None) -> datetime | None:
        """Reject naive or non-UTC timestamps."""
        if value is not None:
            if value.tzinfo is None or value.utcoffset() != timedelta(0):
                raise ValueError("resolved_at must be a tz-aware UTC datetime")
        return value

    @model_validator(mode="after")
    def _require_resolved_at_coherence(self) -> "StatusProposal":
        """Enforce that resolved_at is set iff state is terminal."""
        if self.state == ProposalState.OPEN:
            if self.resolved_at is not None:
                raise ValueError("open state requires resolved_at to be None")
        else:
            if self.resolved_at is None:
                raise ValueError(
                    f"{self.state.value} state requires resolved_at to be set"
                )
        return self

    @property
    def terminal(self) -> bool:
        """True if the proposal is in a terminal state."""
        return self.state != ProposalState.OPEN


def is_valid_transition(from_state: ProposalState, to_state: ProposalState) -> bool:
    """Determine if a transition from one state to another is allowed (dossier §12).

    Transitions are only allowed from open to any terminal state.
    Terminal states are final and cannot transition further.
    """
    if from_state == ProposalState.OPEN:
        return to_state != ProposalState.OPEN
    return False
