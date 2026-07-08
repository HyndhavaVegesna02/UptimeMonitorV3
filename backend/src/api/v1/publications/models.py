"""Pydantic DTOs for the publications API feature (dossier §9, §12/T1.1, §17, STORY-072)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PublicationDTO(BaseModel):
    """Data Transfer Object representing a recorded publish ATTEMPT.

    Distinct from the `Publication` domain type — this is the HTTP surface.
    Fields: component_id, status, published_at, proposal_id, outcome, id.
    """

    model_config = ConfigDict(frozen=True)

    id: int
    """Database-assigned surrogate key."""

    component_id: str
    """The canonical component id."""

    status: str
    """The status that was (attempted to be) published (as a string, e.g. 'operational')."""

    published_at: datetime
    """Instant the publish attempt was recorded (tz-aware UTC)."""

    proposal_id: int | None
    """The status_proposal that triggered this publish, if any."""

    outcome: str
    """Whether the Statuspage publish succeeded or failed (STORY-072: 'succeeded'/'failed')."""
