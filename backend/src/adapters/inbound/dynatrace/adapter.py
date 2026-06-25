"""The Dynatrace adapter entry point (dossier §8) — STORY-009's pull loop calls
this.

`fetch_observations` ties the three pieces of this package together for one
pull cycle against one monitor: build the DQL query scoped to the watermark +
overlap window, run it through the injected `Executor` seam (never a live
call inside this package or its tests), and dispatch every returned row to
its monitor-type normalizer. The result is a flat list of canonical
`SignalObservation`s — one per location execution, never aggregated — ready
to hand to `SignalIngestPort.ingest_observations` (dossier §6, §8).
"""

from datetime import datetime, timedelta

from src.core.domain import SignalObservation

from src.adapters.inbound.dynatrace.dispatch import normalize_rows
from src.adapters.inbound.dynatrace.query import Executor, build_dql_query

#: Default overlap window (dossier §8): re-read this much before the
#: watermark on every pull so a slow-to-land row is never missed.
DEFAULT_OVERLAP = timedelta(minutes=5)


def fetch_observations(
    *,
    signal_key: str,
    native_id: str,
    watermark: datetime | None,
    executor: Executor,
    overlap: timedelta = DEFAULT_OVERLAP,
) -> list[SignalObservation]:
    """Run one pull cycle for one monitor and return canonical observations.

    `native_id` is the vendor monitor id being polled; `signal_key` is the
    canonical name we assign its observations. `executor` is the injected
    DQL-running seam (dossier §8) — production wiring (composition root)
    supplies a real one, tests supply a fake. Raises
    `dispatch.UnsupportedMonitorTypeError` if any returned row's monitor type
    has no registered normalizer (AC5) — the caller decides how to handle
    that (e.g. quarantine the cycle) rather than this function guessing.
    """
    query = build_dql_query(native_id=native_id, watermark=watermark, overlap=overlap)
    rows = executor(query)
    return normalize_rows(rows, signal_key=signal_key)
