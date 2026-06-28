"""Pydantic HTTP DTOs for decisions (api/v1/decisions zone).

Cites dossier §13.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DecisionRequest(BaseModel):
    """DTO for the incoming decision request."""

    model_config = ConfigDict(frozen=True)

    action: str
    actor: str
    notes: str | None = None


class DecisionResponse(BaseModel):
    """DTO for the outgoing decision response."""

    model_config = ConfigDict(frozen=True)

    proposal_id: int
    state: str
    resolved_at: datetime
