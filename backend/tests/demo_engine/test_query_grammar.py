"""STORY-148 AC3/AC4 — the ingest DQL grammar, parsed and honoured in full.

`build_dql_query` (`adapters/inbound/dynatrace/query.py:85-97`) is the REAL,
unmodified production function under test here: these tests build queries
through it and prove the demo engine's row store honours all THREE clauses
(monitor id, `event.type`, and the watermark lower bound when present), not
two, and that the watermark bound is PARSED rather than string-compared.
"""

from datetime import datetime, timedelta, timezone

from demo_engine.rows import build_row, format_ns_timestamp
from demo_engine.store import DemoRowStore
from src.adapters.inbound.dynatrace.query import build_dql_query

_T0 = datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc)


def test_ingest_query_scopes_to_monitor_and_event_type_and_sorts_ascending():
    store = DemoRowStore()
    row_a_later = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="2",
        timestamp=format_ns_timestamp(_T0 + timedelta(minutes=2)),
    )
    row_a_earlier = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="1",
        timestamp=format_ns_timestamp(_T0 + timedelta(minutes=1)),
    )
    row_b = build_row(
        monitor_id="MON-B",
        location="LOC-1",
        event_id="3",
        timestamp=format_ns_timestamp(_T0),
    )
    row_wrong_event_type = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="4",
        timestamp=format_ns_timestamp(_T0),
        event_type="http_step_execution",
    )
    for row in (row_a_later, row_a_earlier, row_b, row_wrong_event_type):
        store.add_row(row)

    query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
    results = store.handle_query(query)

    # monitor B's row and the wrong-event.type row are both excluded; the
    # two matching rows come back sorted `timestamp asc`, per the query.
    assert [row["event.id"] for row in results] == ["1", "2"]


def test_ingest_query_watermark_bound_excludes_older_rows():
    store = DemoRowStore()
    older = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="old",
        timestamp=format_ns_timestamp(_T0 - timedelta(minutes=1)),
    )
    newer = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="new",
        timestamp=format_ns_timestamp(_T0 + timedelta(minutes=1)),
    )
    store.add_row(older)
    store.add_row(newer)

    query = build_dql_query(native_id="MON-A", watermark=_T0, overlap=timedelta(0))
    results = store.handle_query(query)

    assert [row["event.id"] for row in results] == ["new"]


def test_ingest_query_with_no_watermark_returns_everything_for_the_monitor():
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="1",
            timestamp=format_ns_timestamp(_T0 - timedelta(days=10)),
        )
    )

    query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
    results = store.handle_query(query)

    assert [row["event.id"] for row in results] == ["1"]
