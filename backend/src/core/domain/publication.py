"""Publication domain type (dossier §9, §12/T1.1, §17, STORY-072).

A `Publication` records an approve publish ATTEMPT, independent of whether the
Statuspage publish itself succeeded (STORY-072). Every attempt is recorded
with an `outcome`: SUCCEEDED when the delegate publish returned normally,
FAILED when it raised (e.g. a Statuspage 401) -- the raise still propagates
to the caller (see `RecordingPublisher`), so this table is the durable,
independent audit trail even when the external publish itself is best-effort
and swallowed further out. The Publications tab (§17) reads from this table
to display publish history, now including failed attempts.
"""

from datetime import datetime, timedelta
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

from src.core.domain.status import ComponentStatus


class PublicationOutcome(str, Enum):
    """Closed set of outcomes for a recorded publish attempt (STORY-072).

    Distinct from `ComponentStatus` (the health status attempted to publish):
    this is whether the Statuspage call itself succeeded or raised.
    """

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Publication(BaseModel):
    """A recorded Statuspage publish ATTEMPT (dossier §9, §12/T1.1, §17, STORY-072).

    Frozen read model: written once by `PostgresPublicationRepository.record`,
    read back by `list_recent` to back the Publications tab (§17).

    Fields:
        component_id: The canonical component id.
        status: The status that was (attempted to be) published.
        published_at: Tz-aware UTC instant of the publish attempt (validated).
        proposal_id: The status_proposal that triggered this publish, if any.
        outcome: Whether the Statuspage publish succeeded or failed. Defaults
            to SUCCEEDED -- matching the STORY-072 migration backfill for
            every historical row (recorded only on success, under the old
            success-only path) -- but production code (`RecordingPublisher`)
            always sets this explicitly on both the success and failure path.
        id: Database-assigned PK; None before persistence.
    """

    model_config = ConfigDict(frozen=True)

    component_id: str
    """The canonical component id (FK → components.id)."""

    status: ComponentStatus
    """The status that was (attempted to be) published."""

    published_at: datetime
    """Instant the publish attempt was recorded (tz-aware UTC, validated at construction)."""

    proposal_id: int | None = None
    """FK → status_proposals.id; None for publishes not triggered by a proposal."""

    outcome: PublicationOutcome = PublicationOutcome.SUCCEEDED
    """Whether the Statuspage publish succeeded or failed (STORY-072)."""

    id: int | None = None
    """Database-assigned surrogate key; None before persisted."""

    @field_validator("published_at")
    @classmethod
    def _require_published_at_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC published_at timestamps (mirrors maintenance.py pattern)."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("published_at must be a tz-aware UTC datetime")
        return value
