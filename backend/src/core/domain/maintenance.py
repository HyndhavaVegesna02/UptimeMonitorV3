"""Maintenance window domain models (dossier §9, §10, §17)."""

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class MaintenanceWindow(BaseModel):
    """A scheduled maintenance window for a component (dossier §9, §10, §17)."""

    model_config = ConfigDict(frozen=True)

    component_id: str
    """The component under maintenance."""

    starts_at: datetime
    """Start time of the maintenance window (tz-aware UTC)."""

    ends_at: datetime
    """End time of the maintenance window (tz-aware UTC)."""

    reason: str | None = None
    """Optional explanation for the maintenance."""

    id: int | None = None
    """Optional database ID if persisted."""

    @field_validator("starts_at")
    @classmethod
    def _require_starts_at_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC starts_at timestamps."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("starts_at must be a tz-aware UTC datetime")
        return value

    @field_validator("ends_at")
    @classmethod
    def _require_ends_at_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC ends_at timestamps."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("ends_at must be a tz-aware UTC datetime")
        return value

    @model_validator(mode="after")
    def _require_ends_after_starts(self) -> "MaintenanceWindow":
        """Enforce the ends_at > starts_at invariant."""
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be strictly greater than starts_at")
        return self
