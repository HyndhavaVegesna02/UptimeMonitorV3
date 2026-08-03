"""In-memory Grail-shaped row store + query dispatch (STORY-148 AC3-AC5).

Answers the two DQL grammars the production code emits by filtering an
in-memory row list. This story ships no scenario player (that's STORY-176) —
callers (tests, and the HTTP server in `server.py`) seed rows directly via
`add_row`.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone

from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp

from demo_engine.query_grammar import IngestQuery, VendorHealthQuery, parse_query

#: Mirrors `_HEALTH_CHECK_WINDOW` (`adapters/inbound/dynatrace/query.py:133`,
#: `"2h"`; relocated there from `composition/vendor_health.py:37` at
#: STORY-204, ZR-8 finding 2) — kept as a literal constant here (not
#: imported) because the window is part of the WIRE CONTRACT this engine
#: answers, not an implementation detail borrowed from the adapter that
#: builds the query.
VENDOR_HEALTH_WINDOW = timedelta(hours=2)


class DemoRowStore:
    """Holds Grail-shaped rows and answers both DQL grammars against them."""

    def __init__(self, rows: Sequence[dict] | None = None) -> None:
        self._rows: list[dict] = list(rows) if rows else []

    def add_row(self, row: dict) -> None:
        """Append one Grail-shaped row (e.g. from `rows.build_row`)."""
        self._rows.append(row)

    def handle_query(
        self, query: str, *, request_instant: datetime | None = None
    ) -> list[dict]:
        """Answer one DQL query string against the stored rows.

        `request_instant` is the "now" the vendor-health `from:now()-2h`
        window (STORY-148 AC5) is computed relative to. It defaults to the
        REAL wall clock, read fresh on every call — never a value fixed at
        store-construction time — so the window tracks the REQUEST instant,
        not "how long this engine has been running". The clock is read only
        for a vendor-health query: an ingest query never uses it, so reading
        it unconditionally on every call (STORY-180 minor 7) was a wasted
        read on the far more common path.
        """
        parsed = parse_query(query)
        if isinstance(parsed, VendorHealthQuery):
            instant = (
                request_instant
                if request_instant is not None
                else datetime.now(timezone.utc)
            )
            return self._answer_vendor_health(parsed, request_instant=instant)
        return self._answer_ingest(parsed)

    def _answer_ingest(self, parsed: IngestQuery) -> list[dict]:
        matched = [
            row
            for row in self._rows
            if row.get("dt.synthetic.monitor.id") == parsed.monitor_id
            and row.get("event.type") == parsed.event_type
            and (
                parsed.since is None
                or parse_ns_timestamp(row["timestamp"]) >= parsed.since
            )
        ]
        matched.sort(key=lambda row: parse_ns_timestamp(row["timestamp"]))
        return matched

    def _answer_vendor_health(
        self, parsed: VendorHealthQuery, *, request_instant: datetime
    ) -> list[dict]:
        window_start = request_instant - VENDOR_HEALTH_WINDOW
        count = sum(
            1
            for row in self._rows
            if row.get("dt.synthetic.monitor.id") == parsed.monitor_id
            and window_start <= parse_ns_timestamp(row["timestamp"]) <= request_instant
        )
        return [{"count()": count}]
