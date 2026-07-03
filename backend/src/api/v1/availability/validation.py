"""Syntactic validation for the availability read endpoints (dossier §13).

Uses stdlib only. Raises structured errors → 422 before any core call.
"""

from datetime import datetime


class SyntacticValidationError(ValueError):
    """Raised when incoming request fails syntactic validation."""


def _validate_optional_tz_aware(label: str, value: str | None) -> None:
    """Parse `value` as ISO-8601 and require tz-awareness, when supplied.

    Shared by both availability validators (2026-06-25 share-the-assembly
    agreement) so the naive-datetime → 422 rule (2026-06-28 agreement) has
    ONE home instead of being copy-pasted per endpoint.
    """
    if value is None:
        return
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as e:
        raise SyntacticValidationError(
            f"{label} must be a parseable ISO-8601 datetime string: {e}"
        ) from e
    if parsed.tzinfo is None:
        raise SyntacticValidationError(f"{label} must be timezone-aware.")


def validate_availability_request(
    *,
    signal_key: str,
    since: str | None,
    until: str | None,
    interval_seconds: int | None,
) -> None:
    """Perform syntactic validation on per-signal availability query parameters.

    Ensures:
    - signal_key is a non-empty string.
    - since/until (if provided) are parseable, tz-aware ISO-8601 strings.
    - interval_seconds (if provided) is a positive integer.
    """
    if not signal_key or not signal_key.strip():
        raise SyntacticValidationError("signal_key must be a non-empty string.")

    _validate_optional_tz_aware("since", since)
    _validate_optional_tz_aware("until", until)

    if interval_seconds is not None and interval_seconds <= 0:
        raise SyntacticValidationError("interval_seconds must be a positive integer.")


def validate_component_availability_request(
    *,
    component_id: str,
    since: str | None,
    until: str | None,
) -> None:
    """Perform syntactic validation on component-availability query parameters
    (dossier §11, §13, STORY-044 AC2).

    Ensures:
    - component_id is a non-empty string.
    - since/until (if provided) are parseable, tz-aware ISO-8601 strings
      (2026-06-28 agreement: a naive datetime is a 422, not a core-layer
      crash).

    No `interval_seconds` param here — each child signal uses its OWN
    configured interval (D4), so there is nothing to validate on that axis.
    """
    if not component_id or not component_id.strip():
        raise SyntacticValidationError("component_id must be a non-empty string.")

    _validate_optional_tz_aware("since", since)
    _validate_optional_tz_aware("until", until)
