"""Syntactic validation for maintenance scheduling (api/v1/maintenance feature).

Uses stdlib only. Cites dossier §13.
"""

from datetime import datetime


class SyntacticValidationError(ValueError):
    """Raised when incoming request fails syntactic validation."""


def validate_maintenance_request(
    *, component_id: str, starts_at: datetime, ends_at: datetime
) -> None:
    """Perform syntactic validation on the maintenance scheduling parameters.

    Checks, in order: component_id non-empty, both timestamps tz-aware, then
    ends_at strictly after starts_at. The ordering check lives here (rather
    than only in the domain `MaintenanceWindow` model-validator, dossier
    §9/§10) so the 422 fires with a clean one-line message BEFORE domain
    construction — the domain validator's `ValueError` renders as a raw
    Pydantic multi-line blob when `service.py` step 2 does `str(e)`
    (STORY-052). The domain check stays as defense in depth.
    """
    if not component_id.strip():
        raise SyntacticValidationError("component_id must be a non-empty string.")

    if starts_at.tzinfo is None:
        raise SyntacticValidationError("starts_at must be timezone-aware.")

    if ends_at.tzinfo is None:
        raise SyntacticValidationError("ends_at must be timezone-aware.")

    if ends_at <= starts_at:
        raise SyntacticValidationError(
            "ends_at must be strictly greater than starts_at."
        )
