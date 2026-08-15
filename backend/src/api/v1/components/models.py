"""Pydantic DTOs for components (api/v1/components feature).

Cites dossier §13, §17.
"""

from pydantic import BaseModel, ConfigDict


class ComponentDTO(BaseModel):
    """Data Transfer Object representing a component for frontend consumption."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    status: str
    group: str | None = None
    description: str | None = None
