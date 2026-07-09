"""Syntactic validation for maintenance scheduling (api/v1/maintenance feature).

Cites dossier §13. `SyntacticValidationError` is re-exported here for
back-compat (STORY-075, Proposal (2026-07-10) §6.2/§6.4) — it is now defined
once in `_shared/validation.py` so `_shared/errors.py` can map it to HTTP 422
without importing this feature package.
"""

from datetime import datetime, timedelta

from src.api.v1._shared.validation import SyntacticValidationError

__all__ = ["SyntacticValidationError", "validate_maintenance_request"]


def validate_maintenance_request(
    *, component_id: str, starts_at: datetime, ends_at: datetime
) -> None:
    """Perform syntactic validation on the maintenance scheduling parameters.

    Checks, in order: component_id non-empty, both timestamps tz-aware, both
    timestamps in UTC (STORY-075: a tz-aware-but-non-UTC offset, e.g. `+05:30`,
    used to slip past this syntactic layer and get caught only by the domain
    `MaintenanceWindow` validator, whose re-wrapped `pydantic.ValidationError`
    then rendered as a raw multi-line blob once the base `ValueError` 422
    catch-all was removed from `_shared/errors.py` — closed here so it stays a
    clean one-line 422 at the edge), then ends_at strictly after starts_at.
    The ordering check lives here (rather than only in the domain
    `MaintenanceWindow` model-validator, dossier §9/§10) so the 422 fires with
    a clean one-line message BEFORE domain construction — the domain
    validator's `ValueError` renders as a raw Pydantic multi-line blob when
    `service.py` step 2 does `str(e)` (STORY-052). The domain checks stay as
    defense in depth.
    """
    if not component_id.strip():
        raise SyntacticValidationError("component_id must be a non-empty string.")

    if starts_at.tzinfo is None:
        raise SyntacticValidationError("starts_at must be timezone-aware.")

    if starts_at.utcoffset() != timedelta(0):
        raise SyntacticValidationError("starts_at must be in UTC.")

    if ends_at.tzinfo is None:
        raise SyntacticValidationError("ends_at must be timezone-aware.")

    if ends_at.utcoffset() != timedelta(0):
        raise SyntacticValidationError("ends_at must be in UTC.")

    if ends_at <= starts_at:
        raise SyntacticValidationError(
            "ends_at must be strictly greater than starts_at."
        )
