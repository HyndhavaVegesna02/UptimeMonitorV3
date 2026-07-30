"""Normalizer dispatch (dossier §5, §7) — routes each DQL row to its monitor-type
normalizer and flattens the results.

Each HTTP monitor execution in Dynatrace Grail emits two event types sharing
the same `event.id` and `timestamp`:

- ``http_monitor_execution`` — the canonical per-run overall verdict; this is
  the row the query fetches (``build_dql_query`` filters to it via
  ``event.type == "http_monitor_execution"``; dossier §8, STORY-016c).
- ``http_step_execution``  — the per-step companion row; excluded at the source
  by the query filter so it is never dispatched in production. It is omitted
  from this registry to state intent clearly (see AC5 test for the dedup
  demonstration).

This registry is the seam that keeps adding a future normalizer purely
additive: it maps a vendor ``event.type`` string to the normalizer function
for that type. Dispatch never aggregates — the output is one canonical
``SignalObservation`` per input row (per location execution), in input order,
regardless of how many distinct monitors or locations are mixed in the same DQL
response (dossier §5 normalization rules).

An unmapped ``event.type`` raises ``UnsupportedMonitorTypeError`` (fail-loud,
defense-in-depth behind the query filter). A row missing ``event.type``
raises ``MalformedDqlRowError``.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from src.adapters.inbound.dynatrace._assembly import (
    MalformedDqlRowError as MalformedDqlRowError,
)
from src.adapters.inbound.dynatrace._assembly import (
    require_field,
)
from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row
from src.core.domain import SignalObservation

#: Vendor ``event.type`` → normalizer for that monitor type.
#:
#: ``http_monitor_execution`` is the canonical row fetched by ``build_dql_query``
#: (dossier §8, STORY-016c). ``http_step_execution`` is excluded at the source
#: by the query filter and is intentionally absent from this registry.
#: Clickpath's real ``event.type`` is unknown/out of scope — do not guess it.
_NORMALIZERS: dict[str, Callable[..., SignalObservation]] = {
    "http_monitor_execution": normalize_http_row,
}


class UnsupportedMonitorTypeError(ValueError):
    """Raised when a DQL row's `event.type` has no registered normalizer.

    Out-of-scope monitor types surface here rather than being silently mis-normalized (AC3).
    """


@dataclass(frozen=True)
class RowNormalizationFailure:
    """Recorded failure when a DQL row cannot be normalized."""

    row: dict
    reason: str


@dataclass(frozen=True)
class NormalizationOutcome:
    """The result of a lenient normalization pass over a batch of DQL rows.

    Carries the rows that normalized (in input order) alongside the ones that
    did not, so the caller can ingest the good and quarantine the bad rather
    than losing the batch to the first failure.
    """

    observations: list[SignalObservation]
    failures: list[RowNormalizationFailure]


def normalize_row(row: dict, *, signal_key: str) -> SignalObservation:
    """Dispatch one DQL row to its monitor-type normalizer.

    Raises `UnsupportedMonitorTypeError` for any `event.type` not in
    `_NORMALIZERS` instead of guessing, and `MalformedDqlRowError`
    if the dispatch key itself is missing from the row.
    """
    monitor_type = require_field(row, "event.type")
    try:
        normalizer = _NORMALIZERS[monitor_type]
    except KeyError:
        raise UnsupportedMonitorTypeError(
            f"unsupported Dynatrace event.type: {monitor_type!r}"
        ) from None
    return normalizer(row, signal_key=signal_key)


def normalize_rows(rows: Sequence[dict], *, signal_key: str) -> list[SignalObservation]:
    """Normalize a sequence of DQL rows into a flat list of observations.

    One observation per row (one per location execution); rows for different
    monitor types or different locations are normalized independently and
    never aggregated together (dossier §5).
    """
    return [normalize_row(row, signal_key=signal_key) for row in rows]


def normalize_rows_lenient(
    rows: Sequence[dict], *, signal_key: str
) -> NormalizationOutcome:
    """Normalize DQL rows into observations while capturing row-level failures.

    Preserves the input order of successfully normalized observations. A row
    that cannot be normalized costs ONLY ITSELF -- the rest of the batch still
    ingests, so the watermark advances past the bad row instead of the signal
    stalling on it forever (STORY-190).

    **Catches `ValueError`, deliberately broadly.** The first version named
    exactly three classes -- `UnknownVendorStatusError`,
    `UnsupportedMonitorTypeError`, `MalformedDqlRowError` -- which closed the
    defect only for a MISSING field, an unmapped `event.type`, and an unknown
    status. A row with a field that is PRESENT BUT INVALID still escaped and
    still killed the whole cycle. Verified live against the real captured
    fixture during the sprint-65 quality review:

        row["timestamp"] = "not-a-timestamp"          -> ValueError
        row["dt.entity.synthetic_location"] = None    -> pydantic ValidationError

    Both propagated out of `fetch_observations`, out of `run_cycle`, and into
    `run_periodic`'s `except Exception` -- the watermark never advanced and the
    signal stalled on the same window every cycle. That is precisely the defect
    this function exists to close, and a vendor shape change emitting a `null`
    location is a realistic trigger.

    `ValueError` is the right net rather than a lucky one: all three named
    errors are `ValueError` subclasses (`UnknownVendorStatusError` and
    `UnknownVendorOutcomeError` in `health_mapping.py`,
    `UnsupportedMonitorTypeError` here, `MalformedDqlRowError` in `_assembly`),
    and pydantic's `ValidationError` is one too. It stays narrower than
    `Exception`, so a programming error (`TypeError`, `AttributeError`) or a
    `KeyboardInterrupt` still surfaces loudly instead of being silently
    recorded as a bad vendor row.
    """
    observations: list[SignalObservation] = []
    failures: list[RowNormalizationFailure] = []
    for row in rows:
        try:
            obs = normalize_row(row, signal_key=signal_key)
            observations.append(obs)
        except ValueError as exc:
            failures.append(RowNormalizationFailure(row=dict(row), reason=str(exc)))
    return NormalizationOutcome(observations=observations, failures=failures)
