"""STORY-148 AC5 — the SECOND query grammar (`summarize count()`).

`build_vendor_health_query` (`composition/vendor_health.py:40-53`) is the
REAL, unmodified production function under test — a different grammar
entirely from the ingest fetch: `fetch dt.synthetic.events, from:now()-2h |
filter dt.synthetic.monitor.id == "…" | summarize count()`, whose response
must be a single row keyed literally `"count()"` (`_extract_count`,
`vendor_health.py:56-76`). `check_vendor_id_health` runs this at every
startup, for every configured signal, BEFORE any loop is built — so an
engine answering only the ingest grammar would make every monitor id look
dead.

The window is `from:now()-2h`, computed relative to the REQUEST instant —
not "how long the engine has been running" — proven below by varying the
request instant against a single, never-reconstructed store.
"""

import re
from datetime import datetime, timedelta, timezone

from demo_engine.rows import build_row, format_ns_timestamp
from demo_engine.store import VENDOR_HEALTH_WINDOW, DemoRowStore
from src.composition.vendor_health import _HEALTH_CHECK_WINDOW, build_vendor_health_query


def test_vendor_health_query_returns_live_count_for_known_monitor_and_zero_for_unknown():
    now = datetime(2026, 7, 29, 12, 0, 0, tzinfo=timezone.utc)
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-KNOWN",
            location="LOC-1",
            event_id="1",
            timestamp=format_ns_timestamp(now - timedelta(minutes=30)),
        )
    )

    known_query = build_vendor_health_query(native_id="MON-KNOWN")
    unknown_query = build_vendor_health_query(native_id="MON-UNKNOWN")

    assert store.handle_query(known_query, request_instant=now) == [{"count()": 1}]
    assert store.handle_query(unknown_query, request_instant=now) == [{"count()": 0}]


def test_vendor_health_window_tracks_the_request_instant_not_engine_construction_time():
    """A row is seeded ONCE, at store-construction time. Querying with a
    request instant close to it (within the 2h window) counts it; querying
    the SAME store with a request instant far past it (outside the window)
    does not — proving the window is computed fresh from the passed request
    instant on every call, never cached from when the store/engine was
    built.
    """
    row_timestamp = datetime(2026, 7, 29, 8, 0, 0, tzinfo=timezone.utc)
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="1",
            timestamp=format_ns_timestamp(row_timestamp),
        )
    )
    query = build_vendor_health_query(native_id="MON-A")

    within_window = row_timestamp + timedelta(hours=1)
    assert store.handle_query(query, request_instant=within_window) == [{"count()": 1}]

    outside_window = row_timestamp + timedelta(hours=5)
    assert store.handle_query(query, request_instant=outside_window) == [{"count()": 0}]


def test_vendor_health_window_matches_the_composition_health_check_window():
    """STORY-180 AC2 (minor 1): `store.py`'s hardcoded `VENDOR_HEALTH_WINDOW`
    must equal `vendor_health.py`'s `_HEALTH_CHECK_WINDOW` -- the composition
    constant this engine's literal is deliberately NOT imported from (it is
    part of the wire contract the engine answers, not borrowed from
    composition; see `store.py:18-22`). Without this test, a future change to
    `_HEALTH_CHECK_WINDOW` would make the demo diverge SILENTLY in the one
    dimension it hardcodes -- this test turns that into a build failure.

    Parses `_HEALTH_CHECK_WINDOW`'s `"<N>h"` shape here, in the TEST only
    (the route decided at planning is the equality test, not teaching the
    engine to parse a DQL `from:` clause -- see STORY-180 AC2).
    """
    match = re.fullmatch(r"(\d+)h", _HEALTH_CHECK_WINDOW)
    assert match is not None, (
        f"unexpected _HEALTH_CHECK_WINDOW format: {_HEALTH_CHECK_WINDOW!r}"
    )
    assert VENDOR_HEALTH_WINDOW == timedelta(hours=int(match.group(1)))


def test_vendor_health_query_defaults_request_instant_to_the_real_wall_clock():
    """Without an explicit `request_instant`, the store uses the REAL
    current time — so a row seeded "recently" relative to actual wall-clock
    now (not relative to when the store object was constructed) is counted.
    """
    now = datetime.now(timezone.utc)
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="1",
            timestamp=format_ns_timestamp(now - timedelta(hours=1)),
        )
    )

    query = build_vendor_health_query(native_id="MON-A")
    assert store.handle_query(query) == [{"count()": 1}]
