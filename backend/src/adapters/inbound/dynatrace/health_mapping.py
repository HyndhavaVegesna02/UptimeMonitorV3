"""Vendor health mapping (dossier §5, §7) — the ONLY place vendor status words
are read.

Two explicit, unit-tested translations to the canonical `Health` enum (dossier
§5, closed + not pass/fail so a partial outage is expressible):

- `map_synthetic_status(code, message)` — the LIVE HTTP path (STORY-016b, STORY-177).
  Real `dt.synthetic.events` rows carry `result.status.code` / `result.status.message`
  (e.g. `"0"` / `"HEALTHY"`). Healthy rows map to `Health.UP`. Non-healthy rows are checked
  against an explicit provisional mapping (`PROVISIONAL_STATUS_MAPPING`) pending live
  trial verification (STORY-154, superseded trial expiry 2026-07-28). Unrecognized
  pairs raise `UnknownVendorStatusError` (fail-loud).
- `map_execution_outcome(outcome)` — the legacy `execution.outcome`
  (`success`/`failure`/`partial`) path, still used by `clickpath_normalizer`
  (browser clickpath is out of the live HTTP scope; retained, not exercised by
  the live dispatch).

Every normalizer calls through here rather than re-deriving a mapping.
"""

import logging

from src.core.domain import Health

logger = logging.getLogger(__name__)

_OUTCOME_TO_HEALTH = {
    "success": Health.UP,
    "failure": Health.DOWN,
    "partial": Health.DEGRADED,
}

#: UNVERIFIED provisional failure mapping (STORY-177).
#: Pending live verification upon Dynatrace trial renewal (STORY-154).
PROVISIONAL_STATUS_MAPPING: dict[tuple[str, str], Health] = {
    ("1", "UNHEALTHY"): Health.DOWN,
    ("2", "DEGRADED"): Health.DEGRADED,
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
    """Translate a Dynatrace synthetic `result.status` code/message to canonical Health (STORY-016b, STORY-177).

    1. Healthy OR-rule (first and unchanged): `code == "0"` or `message == "HEALTHY"` -> `Health.UP`.
    2. Provisional lookup: exact `(code, message)` tuple match in `PROVISIONAL_STATUS_MAPPING`.
       Logs a loud WARNING naming code, message, and provisional status pending STORY-154.
    3. Any unmapped tuple raises `UnknownVendorStatusError` (fail-loud).
    """
    if code == "0" or message == "HEALTHY":
        return Health.UP

    if (code, message) in PROVISIONAL_STATUS_MAPPING:
        health = PROVISIONAL_STATUS_MAPPING[(code, message)]
        logger.warning(
            "Provisional status mapping hit for code=%r, message=%r -> %s (unverified pending STORY-154)",
            code,
            message,
            health.name,
        )
        return health

    raise UnknownVendorStatusError(
        f"unknown Dynatrace synthetic status: code={code!r}, message={message!r}"
    )
