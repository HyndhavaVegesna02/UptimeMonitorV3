"""Syntactic validation for maintenance scheduling (api/v1/maintenance feature).

Uses stdlib only. Cites dossier §13.
"""

from datetime import datetime


class SyntacticValidationError(ValueError):
    """Raised when incoming request fails syntactic validation."""


def validate_maintenance_request(
    *, component_id: str, starts_at: datetime, ends_at: datetime
) -> None:
    """Perform syntactic validation on the maintenance scheduling parameters."""
    if not component_id.strip():
        raise SyntacticValidationError("component_id must be a non-empty string.")

    if starts_at.tzinfo is None:
        raise SyntacticValidationError("starts_at must be timezone-aware.")

    if ends_at.tzinfo is None:
        raise SyntacticValidationError("ends_at must be timezone-aware.")
