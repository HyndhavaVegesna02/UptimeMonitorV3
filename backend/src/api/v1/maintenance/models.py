"""Pydantic DTOs for the maintenance API feature (dossier §13, §17)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaintenanceWindowDTO(BaseModel):
    """Data Transfer Object representing a scheduled maintenance window."""

    model_config = ConfigDict(frozen=True)

    id: int
    component_id: str
    starts_at: datetime
    ends_at: datetime
    reason: str | None
    title: str | None = None


class CreateMaintenanceRequest(BaseModel):
    """Data Transfer Object for scheduling a new maintenance window."""

    model_config = ConfigDict(frozen=True)

    component_id: str
    starts_at: datetime
    ends_at: datetime
    reason: str | None = None
    title: str | None = None
