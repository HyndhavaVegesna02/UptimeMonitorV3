"""Vendor health mapping (dossier §5, §7) — the ONLY place vendor outcome words
are read.

Dynatrace synthetic executions report an `execution.outcome` of `success`,
`failure`, or `partial`. The canonical `Health` enum (dossier §5) is closed
and not pass/fail, so a partial outage is expressible. This module is the
single explicit, unit-tested translation from vendor outcome to canonical
`Health`; every normalizer in this package calls through it rather than
re-deriving the mapping.
"""

from src.core.domain import Health

_OUTCOME_TO_HEALTH = {
    "success": Health.UP,
    "failure": Health.DOWN,
    "partial": Health.DEGRADED,
}


class UnknownVendorOutcomeError(ValueError):
    """Raised when a vendor `execution.outcome` is not one of the mapped values."""


def map_execution_outcome(outcome: str) -> Health:
    """Translate a Dynatrace `execution.outcome` string to canonical `Health`.

    Explicit and total over the three documented outcomes
    (`success` / `failure` / `partial`); an unrecognized value raises rather
    than silently defaulting, so a vendor change surfaces immediately instead
    of mis-normalizing (dossier §5 normalization rules).
    """
    try:
        return _OUTCOME_TO_HEALTH[outcome]
    except KeyError:
        raise UnknownVendorOutcomeError(
            f"unknown Dynatrace execution.outcome: {outcome!r}"
        ) from None


class UnknownVendorStatusError(ValueError):
    """Raised when a vendor status code or message is not recognized (STORY-016b)."""


def map_synthetic_status(*, code: str, message: str) -> Health:
    """Translate a Dynatrace synthetic status code and message to canonical Health (STORY-016b).

    Unrecognized code/message raises UnknownVendorStatusError rather than silently defaulting.
    """
    if code == "0" or message == "HEALTHY":
        return Health.UP

    raise UnknownVendorStatusError(
        f"unknown Dynatrace synthetic status: code={code!r}, message={message!r}"
    )
