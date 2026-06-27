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
from src.adapters.inbound.dynatrace.clickpath_normalizer import (
    normalize_clickpath_row,
)
from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row
from src.core.domain import SignalObservation

#: Vendor `synthetic_test.type` -> normalizer for that monitor type.
#: Adding a future type (single-browser, NAM) means adding one entry here and
#: its own normalizer module — no existing normalizer or call site changes.
_NORMALIZERS: dict[str, Callable[..., SignalObservation]] = {
    "HTTP_CHECK": normalize_http_row,
    "BROWSER_CLICKPATH": normalize_clickpath_row,
}


class UnsupportedMonitorTypeError(ValueError):
    """Raised when a DQL row's `synthetic_test.type` has no registered normalizer.

    Out-of-scope monitor types (single-browser, NAM) surface here rather than
    being silently mis-normalized by the wrong normalizer (AC5).
    """


def normalize_row(row: dict, *, signal_key: str) -> SignalObservation:
    """Dispatch one DQL row to its monitor-type normalizer.

    Raises `UnsupportedMonitorTypeError` for any `synthetic_test.type` not in
    `_NORMALIZERS` (e.g. `BROWSER`, `NAM`) instead of guessing, and
    `MalformedDqlRowError` (STORY-020) if the dispatch key itself is missing
    from the row.
    """
    monitor_type = require_field(row, "synthetic_test.type")
    try:
        normalizer = _NORMALIZERS[monitor_type]
    except KeyError:
        raise UnsupportedMonitorTypeError(
            f"unsupported Dynatrace synthetic_test.type: {monitor_type!r}"
        ) from None
    return normalizer(row, signal_key=signal_key)


def normalize_rows(rows: Sequence[dict], *, signal_key: str) -> list[SignalObservation]:
    """Normalize a sequence of DQL rows into a flat list of observations.

    One observation per row (one per location execution); rows for different
    monitor types or different locations are normalized independently and
    never aggregated together (dossier §5).
    """
    return [normalize_row(row, signal_key=signal_key) for row in rows]
