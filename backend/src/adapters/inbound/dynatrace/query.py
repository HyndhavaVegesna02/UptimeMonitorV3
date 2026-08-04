"""DQL query builder + the injected live-executor seam (dossier §8).

`build_dql_query` is a pure function: given a vendor monitor id, the current
per-signal watermark (or `None` if it has never advanced), and an overlap
window, it returns the DQL query string scoped to that one monitor and to
"newer than watermark, with overlap" — never the bare watermark, so a
slow-to-land row just before the cursor is never missed (dossier §8,
"overlap on read + commit-before-advance + dedupe on write = lose nothing").

The query always adds `event.type == "http_monitor_execution"` alongside the
monitor-id scope filter. This is the single live HTTP monitor event type: each
execution emits one canonical `http_monitor_execution` row (the per-run
overall verdict) plus one `http_step_execution` companion that shares the same
`event.id`; the step row is excluded at the source so no two observations ever
collide on the same idempotency key (the `EVT#<event_id>`/`DEDUPE` marker
item, `adapters/persistence/dynamo_observation_repository.py:58-62`).
Parameterizing the fetched
`event.type` per monitor type is explicitly out of scope (STORY-016c) — only
the HTTP monitor is live; clickpath/browser remain future work.

`build_vendor_health_dql` is the OTHER DQL shape this module builds: a cheap,
bounded-window existence probe scoped to one monitor id, unrelated to the
watermark/overlap ingest fetch above (STORY-070). It was relocated here from
`composition/vendor_health.py` at STORY-204 (ZR-8 finding 2: query-
construction logic lives in exactly ONE adapter, and composition calls it
rather than re-implementing it) -- before the move, composition's copy
interpolated `native_id` with no breaking-character validation, silently
building a malformed query instead of raising. Both builders now share
`_reject_dql_breaking_native_id`, so a `native_id` misconfiguration is
rejected identically wherever it is interpolated.

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

#: Characters that would break out of the `"{native_id}"` DQL string literal
#: if interpolated unescaped (STORY-021).
_DQL_BREAKING_CHARS = ('"', "\\", "\n", "\r")


class InvalidNativeIdError(ValueError):
    """Raised when `native_id` contains a character that would break the DQL
    filter string literal it is interpolated into (STORY-021).

    `native_id` is trusted vendor config (the monitor id we configured in
    Dynatrace), not end-user input, so this is a misconfiguration rather than
    an attack — but a breaking character (e.g. `"`) must surface loudly
    instead of silently malforming the query.
    """


def _reject_dql_breaking_native_id(native_id: str) -> None:
    """Raise `InvalidNativeIdError` if `native_id` would break out of the
    `"{native_id}"` DQL string literal it is interpolated into (STORY-021).

    `native_id` is trusted vendor config, not end-user input, and every query
    built in this module is a read-only Grail fetch, so there is no injection
    vector here -- a breaking character (e.g. `"`) would still silently
    malform the query, so it is rejected rather than escaped/sanitized.

    Shared by every DQL builder in this module (STORY-204, ZR-8 finding 2) so
    a `native_id` misconfiguration is caught identically wherever it is
    interpolated, instead of another zone re-implementing this check without
    it.
    """
    if any(char in native_id for char in _DQL_BREAKING_CHARS):
        raise InvalidNativeIdError(
            f"native_id contains a DQL-breaking character: {native_id!r}"
        )


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

    _reject_dql_breaking_native_id(native_id)

    # `event.type == "http_monitor_execution"` scopes to the canonical per-run
    # row, excluding the same-event.id `http_step_execution` companion that
    # Dynatrace emits alongside it (dossier §8, STORY-016c).
    clauses = [
        f'dt.synthetic.monitor.id == "{native_id}"',
        'event.type == "http_monitor_execution"',
    ]
    if watermark is not None:
        since = watermark - overlap
        # toTimestamp() is load-bearing: DQL compares a bare string literal
        # against the timestamp field without coercion and silently matches
        # NOTHING, so a bare-string bound returns 0 rows and the loop
        # permanently stalls after its first (watermark-less) cycle
        # (STORY-051, live-confirmed 2026-07-04).
        since_iso = since.isoformat().replace("+00:00", "Z")
        clauses.append(f'timestamp >= toTimestamp("{since_iso}")')

    filter_expr = " AND ".join(clauses)
    return f"fetch dt.synthetic.events\n| filter {filter_expr}\n| sort timestamp asc"


#: Bounded recent window for `build_vendor_health_dql`'s drift-detection
#: probe (dossier §8, STORY-070 "Decided" section: "a recent bounded window
#: (e.g. last ~2h ...)"; relocated here from `composition/vendor_health.py`
#: at STORY-204). Kept separate from `build_dql_query`'s watermark/overlap
#: window above -- this is a cheap existence probe, not an ingest fetch.
#: PUBLIC (STORY-204 fix round): `composition/vendor_health.py` imports this
#: across a module AND zone boundary -- an underscore-private name is not
#: meant to be imported outside its own module, so this is named publicly.
HEALTH_CHECK_WINDOW = "2h"


def build_vendor_health_dql(*, native_id: str) -> str:
    """Build a bounded DQL count query scoped to one monitor id (STORY-070;
    relocated here from `composition/vendor_health.py` at STORY-204, ZR-8
    finding 2 -- query-construction logic lives in exactly ONE adapter).

    Unlike `build_dql_query` above (which scopes to a watermark/overlap range
    and the `http_monitor_execution` event type for the real ingest fetch),
    this is a cheap "does this id exist at all in a recent window" existence
    probe: a plain bounded-time `fetch` filtered to the monitor id,
    summarized to a single row count. Shares `_reject_dql_breaking_native_id`
    with `build_dql_query` above, so a `native_id` misconfiguration raises
    `InvalidNativeIdError` identically on both paths (STORY-204 AC1) --
    previously this builder silently built a malformed query instead.
    """
    _reject_dql_breaking_native_id(native_id)
    return (
        f"fetch dt.synthetic.events, from:now()-{HEALTH_CHECK_WINDOW}\n"
        f'| filter dt.synthetic.monitor.id == "{native_id}"\n'
        "| summarize count()"
    )
