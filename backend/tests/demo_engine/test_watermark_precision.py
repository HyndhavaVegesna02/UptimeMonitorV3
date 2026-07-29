"""STORY-148 AC4 — the watermark bound is PARSED, not string-compared.

`query.py:96` emits `since.isoformat().replace("+00:00", "Z")`, whose
fractional precision varies: `datetime.isoformat()` omits the fraction
entirely when `microsecond == 0` (0-digit) and emits exactly 6 digits
otherwise, while real rows always carry 9 (`...746000000Z`, fixture:4). Any
lexicographic string comparison is wrong ('0' < 'Z' sorts an equal instant
BEFORE a 9-digit row, excluding it) -- proof: plain strings,
`"2026-07-29T10:00:00Z" > "2026-07-29T10:00:00.000000000Z"` ('Z' (0x5A) >
'.' (0x2E)), so a naive compare would wrongly EXCLUDE an equal-instant row
in the 0-digit case, the opposite of the parsed comparison these tests pin
(STORY-180 AC5/minor 3: this used to be its own test asserting only a
stdlib string-ordering fact; folded in here since it exercises no product
code).

These tests pin all three precisions, each asserting a row at the SAME
instant as the bound is included. The 0- and 6-digit cases are reachable
through the real `build_dql_query` and are routed through it (STORY-180
AC3/minor 2) rather than a hand-built literal; the 9-digit case cannot be
(see its own test below).
"""

from datetime import datetime, timedelta, timezone

import pytest
from demo_engine.rows import build_row, format_ns_timestamp
from demo_engine.store import DemoRowStore
from src.adapters.inbound.dynatrace.query import build_dql_query


@pytest.mark.parametrize(
    "watermark",
    [
        # 0-digit fraction (whole-second watermark) — the LIKELIEST demo
        # shape, since cycle arithmetic naturally lands on whole seconds.
        datetime(2026, 7, 29, 10, 0, 0, tzinfo=timezone.utc),
        # 6-digit fraction (non-zero microsecond watermark).
        datetime(2026, 7, 29, 10, 0, 0, 746000, tzinfo=timezone.utc),
    ],
    ids=["0-digit", "6-digit"],
)
def test_watermark_bound_at_each_reachable_precision_includes_a_row_at_the_same_instant(
    watermark,
):
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="on-bound",
            timestamp=format_ns_timestamp(watermark),
        )
    )

    # `overlap=timedelta(0)` is NOT optional here: `build_dql_query` emits
    # `since = watermark - overlap`, and `DEFAULT_OVERLAP` is 5 minutes. Left
    # at the default, the bound would land 5 minutes before the row, the row
    # would be included regardless of how precision is handled, and this
    # test would silently stop discriminating the STORY-051
    # lexicographic-watermark stall it exists to catch (STORY-180 AC3).
    query = build_dql_query(
        native_id="MON-A", watermark=watermark, overlap=timedelta(0)
    )

    results = store.handle_query(query)

    assert [row["event.id"] for row in results] == ["on-bound"]


def test_watermark_bound_at_the_unreachable_9_digit_precision_includes_a_row_at_the_same_instant():
    """The 9-digit fraction bound is never actually emitted by
    `build_dql_query` -- its `since` is a `datetime`, whose max precision is
    microseconds (6 digits) -- so this case needs a hand-built literal
    rather than routing through the real builder (STORY-180 AC3). Kept
    because a real ROW always carries a 9-digit fraction (fixture:4) and the
    parser must accept a 9-digit BOUND too.
    """
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="on-bound",
            timestamp="2026-07-29T10:00:00.746000000Z",
        )
    )

    query = (
        "fetch dt.synthetic.events\n"
        '| filter dt.synthetic.monitor.id == "MON-A" AND '
        'event.type == "http_monitor_execution" AND '
        'timestamp >= toTimestamp("2026-07-29T10:00:00.746000000Z")\n'
        "| sort timestamp asc"
    )

    results = store.handle_query(query)

    assert [row["event.id"] for row in results] == ["on-bound"]
