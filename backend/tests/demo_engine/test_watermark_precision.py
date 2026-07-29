"""STORY-148 AC4 — the watermark bound is PARSED, not string-compared.

`query.py:96` emits `since.isoformat().replace("+00:00", "Z")`, whose
fractional precision varies: `datetime.isoformat()` omits the fraction
entirely when `microsecond == 0` (0-digit) and emits exactly 6 digits
otherwise, while real rows always carry 9 (`...746000000Z`, fixture:4). Any
lexicographic string comparison is wrong ('0' < 'Z' sorts an equal instant
BEFORE a 9-digit row, excluding it), and a fixed six-digit slice is wrong for
the whole-second (0-digit) case — the likeliest demo shape.

These tests pin all three precisions directly against the parsed bound,
each asserting a row at the SAME instant as the bound is included.
"""

import pytest
from demo_engine.rows import build_row
from demo_engine.store import DemoRowStore


def _ingest_query(bound: str) -> str:
    return (
        "fetch dt.synthetic.events\n"
        '| filter dt.synthetic.monitor.id == "MON-A" AND '
        'event.type == "http_monitor_execution" AND '
        f'timestamp >= toTimestamp("{bound}")\n'
        "| sort timestamp asc"
    )


@pytest.mark.parametrize(
    ("bound", "row_timestamp"),
    [
        # 0-digit fraction bound (whole-second watermark) — the LIKELIEST
        # demo shape, since cycle arithmetic naturally lands on whole seconds.
        ("2026-07-29T10:00:00Z", "2026-07-29T10:00:00.000000000Z"),
        # 6-digit fraction bound (non-zero microsecond watermark).
        ("2026-07-29T10:00:00.746000Z", "2026-07-29T10:00:00.746000000Z"),
        # 9-digit fraction bound — never actually emitted by `query.py`
        # (its source is a `datetime`, max microsecond precision), but the
        # parser must handle it too, since a real ROW always carries one.
        ("2026-07-29T10:00:00.746000000Z", "2026-07-29T10:00:00.746000000Z"),
    ],
    ids=["0-digit", "6-digit", "9-digit"],
)
def test_watermark_bound_at_each_precision_includes_a_row_at_the_same_instant(
    bound, row_timestamp
):
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="on-bound",
            timestamp=row_timestamp,
        )
    )

    results = store.handle_query(_ingest_query(bound))

    assert [row["event.id"] for row in results] == ["on-bound"]


def test_a_naive_lexicographic_compare_would_wrongly_exclude_the_0_digit_case():
    """Documents the exact failure mode AC4 exists to catch: `'2026-07-
    29T10:00:00Z' > '2026-07-29T10:00:00.000000000Z'` as PLAIN STRINGS (`'Z'
    (0x5A) > '.' (0x2E)`), so a naive string compare would wrongly EXCLUDE an
    equal-instant row in the 0-digit case — the opposite of AC4's parsed
    comparison, which includes it (proven above).
    """
    assert "2026-07-29T10:00:00Z" > "2026-07-29T10:00:00.000000000Z"
