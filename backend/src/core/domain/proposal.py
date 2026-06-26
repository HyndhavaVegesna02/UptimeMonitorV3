"""Status proposal domain models and states (dossier §12)."""

from datetime import datetime, timedelta
from enum import Enum
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from src.core.domain.status import ComponentStatus


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
                raise ValueError(f"{self.state.value} state requires resolved_at to be set")
        return self
