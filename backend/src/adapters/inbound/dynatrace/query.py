"""DQL query builder + the injected live-executor seam (dossier §8).

`build_dql_query` is a pure function: given a vendor monitor id, the current
per-signal watermark (or `None` if it has never advanced), and an overlap
window, it returns the DQL query string scoped to that one monitor and to
"newer than watermark, with overlap" — never the bare watermark, so a
slow-to-land row just before the cursor is never missed (dossier §8,
"overlap on read + commit-before-advance + dedupe on write = lose nothing").

`Executor` is the thin injected seam for actually running a DQL query against
Dynatrace. Production wiring (composition root) will inject a real HTTP-backed
implementation; every test in this package injects a fake instead — no live
Dynatrace call is ever made in a test (working agreement: pure core,
mockable edges).
"""

from collections.abc import Callable
from datetime import datetime, timedelta

#: A DQL executor: takes the built query string, returns the raw row dicts
#: Dynatrace's `execute query` response would carry. Production implementations
#: do the real HTTP call; tests inject a fake/fixture-backed callable.
Executor = Callable[[str], list[dict]]


def build_dql_query(
    *, native_id: str, watermark: datetime | None, overlap: timedelta
) -> str:
    """Build a DQL query scoped to one monitor + a watermark/overlap range.

    Scopes to `native_id` (the vendor monitor id) always. When `watermark` is
    given, adds a lower time bound at `watermark - overlap` (never the bare
    watermark) so the overlap window covers rows that land late. When
    `watermark` is `None` (the signal has never been ingested), no lower time
    bound is added — the first pull reads everything DQL returns for the
    monitor.

    `watermark`, like every UTC instant that crosses into this adapter, must
    be tz-aware UTC; a naive datetime is rejected rather than silently
    treated as UTC (mirrors the same rule the core enforces on
    `SignalObservation.observed_at`, dossier §5).
    """
    if watermark is not None and (
        watermark.tzinfo is None or watermark.utcoffset() != timedelta(0)
    ):
        raise ValueError("watermark must be a tz-aware UTC datetime")

    # `native_id` is interpolated unescaped: it is trusted vendor config (the
    # monitor id we configured in Dynatrace, not end-user input), and this
    # query is a read-only Grail fetch, so there is no injection vector here.
    clauses = [f'synthetic_test.id == "{native_id}"']
    if watermark is not None:
        since = watermark - overlap
        clauses.append(f'timestamp >= "{since.isoformat().replace("+00:00", "Z")}"')

    filter_expr = " AND ".join(clauses)
    return (
        "fetch dt.synthetic.executions\n"
        f"| filter {filter_expr}\n"
        "| sort timestamp asc"
    )
