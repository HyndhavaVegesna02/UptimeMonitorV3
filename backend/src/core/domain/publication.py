"""Publication domain type (dossier §9, §12/T1.1, §17).

A `Publication` records a SUCCESSFUL status change that was published to Statuspage.
The table has no error column — only successful publishes are recorded (§12/T1.1:
commit-first, best-effort publish; the publish either succeeds and is recorded, or
it fails and `BestEffortPublisher` logs+swallows without recording). The Publications
tab (§17) reads from this table to display publish history.
"""

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, field_validator

from src.core.domain.status import ComponentStatus


class Publication(BaseModel):
    """A recorded successful Statuspage publish (dossier §9, §12/T1.1, §17).

    Frozen read model: written once by `PostgresPublicationRepository.record`,
    read back by `list_recent` to back the Publications tab (§17).

    Fields:
        component_id: The canonical component id.
        status: The status that was published.
        published_at: Tz-aware UTC instant of the publish (validated).
        proposal_id: The status_proposal that triggered this publish, if any.
        id: Database-assigned PK; None before persistence.
    """

    model_config = ConfigDict(frozen=True)

    component_id: str
    """The canonical component id (FK → components.id)."""

    status: ComponentStatus
    """The status that was successfully published."""

    published_at: datetime
    """Instant the publish was recorded (tz-aware UTC, validated at construction)."""

    proposal_id: int | None = None
    """FK → status_proposals.id; None for publishes not triggered by a proposal."""

    id: int | None = None
    """Database-assigned surrogate key; None before persisted."""

    @field_validator("published_at")
    @classmethod
    def _require_published_at_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC published_at timestamps (mirrors maintenance.py pattern)."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("published_at must be a tz-aware UTC datetime")
        return value
