"""Pydantic DTOs for approvals (api/v1/approvals feature).

Cites dossier §13, §17.
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ProposalDTO(BaseModel):
    """Data Transfer Object representing a status proposal."""

    model_config = ConfigDict(frozen=True)

    id: int
    component_id: str
    from_status: str | None
    to_status: str
    state: str
    proposed_at: datetime
