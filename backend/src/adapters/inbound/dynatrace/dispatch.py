"""Normalizer dispatch (dossier §5, §7) — routes each DQL row to its monitor-type
normalizer and flattens the results.

This is the seam that keeps adding a future normalizer purely additive (AC5):
the registry maps a vendor `synthetic_test.type` string to the normalizer
function for that type. Dispatch never aggregates — the output is one
canonical `SignalObservation` per input row (per location execution), in
input order, regardless of how many distinct monitors or locations are mixed
in the same DQL response (dossier §5 normalization rules).
"""

from collections.abc import Callable, Sequence

from src.adapters.inbound.dynatrace._assembly import (
    MalformedDqlRowError as MalformedDqlRowError,
)
from src.adapters.inbound.dynatrace._assembly import (
    require_field,
)
from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row
from src.core.domain import SignalObservation

#: Vendor `event.type` -> normalizer for that monitor type.
#: Clickpath's real `event.type` is unknown/out of scope (STORY-016b) — do not guess it.
_NORMALIZERS: dict[str, Callable[..., SignalObservation]] = {
    "http_step_execution": normalize_http_row,
}


class UnsupportedMonitorTypeError(ValueError):
    """Raised when a DQL row's `event.type` has no registered normalizer.

    Out-of-scope monitor types surface here rather than being silently mis-normalized (AC3).
    """


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
