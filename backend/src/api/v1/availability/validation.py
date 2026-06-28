"""Syntactic validation for the availability read endpoint (dossier §13).

Uses stdlib only. Raises structured errors → 422 before any core call.
"""

from datetime import datetime


class SyntacticValidationError(ValueError):
    """Raised when incoming request fails syntactic validation."""


def validate_availability_request(
    *,
    signal_key: str,
    since: str | None,
    until: str | None,
    interval_seconds: int | None,
) -> None:
    """Perform syntactic validation on availability query parameters.

    Ensures:
    - signal_key is a non-empty string.
    - since/until (if provided) are parseable ISO-8601 strings.
    - interval_seconds (if provided) is a positive integer.
    """
    if not signal_key or not signal_key.strip():
        raise SyntacticValidationError("signal_key must be a non-empty string.")

    if since is not None:
        try:
            parsed_since = datetime.fromisoformat(since)
        except ValueError as e:
            raise SyntacticValidationError(
                f"since must be a parseable ISO-8601 datetime string: {e}"
            ) from e
        if parsed_since.tzinfo is None:
            raise SyntacticValidationError("since must be timezone-aware.")

    if until is not None:
        try:
            parsed_until = datetime.fromisoformat(until)
        except ValueError as e:
            raise SyntacticValidationError(
                f"until must be a parseable ISO-8601 datetime string: {e}"
            ) from e
        if parsed_until.tzinfo is None:
            raise SyntacticValidationError("until must be timezone-aware.")

    if interval_seconds is not None and interval_seconds <= 0:
        raise SyntacticValidationError("interval_seconds must be a positive integer.")
