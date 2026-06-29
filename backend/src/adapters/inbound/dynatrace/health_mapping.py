"""Vendor health mapping (dossier §5, §7) — the ONLY place vendor status words
are read.

Two explicit, unit-tested translations to the canonical `Health` enum (dossier
§5, closed + not pass/fail so a partial outage is expressible):

- `map_synthetic_status(code, message)` — the LIVE HTTP path (STORY-016b). Real
  `dt.synthetic.events` rows carry `result.status.code` / `result.status.message`
  (e.g. `"0"` / `"HEALTHY"`). Only the healthy value is mapped today; failure /
  degraded codes are added once observed live (the loop fails LOUD on an
  unrecognized value rather than guessing, so the real code surfaces — see the
  STORY-016b plan T6/AC6).
- `map_execution_outcome(outcome)` — the legacy `execution.outcome`
  (`success`/`failure`/`partial`) path, still used by `clickpath_normalizer`
  (browser clickpath is out of the live HTTP scope; retained, not exercised by
  the live dispatch).

Every normalizer calls through here rather than re-deriving a mapping.
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
    """Translate a Dynatrace synthetic `result.status` code/message to canonical Health (STORY-016b).

    Only the known-good value is mapped: `code == "0"` (or `message == "HEALTHY"`)
    -> `Health.UP`. Any other value raises `UnknownVendorStatusError` rather than
    guessing — the live verification (plan T6/AC6) forces the monitor to fail and
    reads the real DOWN/DEGRADED code from this error, and the mapping is extended
    with the observed value(s) THEN. Inventing failure codes here would silently
    mis-map (or mask) the real failure value during that verification, so it is
    deliberately NOT done.
    """
    if code == "0" or message == "HEALTHY":
        return Health.UP

    raise UnknownVendorStatusError(
        f"unknown Dynatrace synthetic status: code={code!r}, message={message!r}"
    )
