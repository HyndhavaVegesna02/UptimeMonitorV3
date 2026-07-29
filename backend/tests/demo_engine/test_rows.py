"""STORY-148 AC1/AC2 — demo row fidelity against the real captured sample.

`backend/tests/fixtures/dynatrace/grail_synthetic_events.json` is the ground
truth: a real Dynatrace Grail `http_monitor_execution` row. These tests
compare a hand-built demo row against it field-by-field, by KEY and VALUE
TYPE — not by eyeballing — and then drive the real, unmodified
`_assembly`/`http_normalizer` production code over a demo row to prove the
optional `duration` field round-trips at the real wire's NANOSECOND scale,
not just its string type.
"""

import json
from datetime import timezone
from pathlib import Path

from demo_engine.rows import build_row

_FIXTURE_PATH = (
    Path(__file__).resolve().parents[1]
    / "fixtures"
    / "dynatrace"
    / "grail_synthetic_events.json"
)

#: The five fields the assembler requires (`_assembly.py:86,108,111,114`) plus
#: `event.type` (dispatch) plus the two the NORMALIZER requires
#: (`http_normalizer.py:22-23`) — seven total, per STORY-148 AC1. A row built
#: to only the assembler's five passes a naive fidelity test and then raises
#: `MalformedDqlRowError` on the first real row through the loop.
REQUIRED_FIELDS = [
    "timestamp",
    "event.id",
    "event.type",
    "dt.synthetic.monitor.id",
    "dt.entity.synthetic_location",
    "result.status.code",
    "result.status.message",
]


def _real_row() -> dict:
    fixture = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
    return fixture["records"][0]


def test_build_row_carries_all_seven_required_fields_matching_fixture_types():
    real_row = _real_row()
    demo_row = build_row(
        monitor_id="HTTP_CHECK-DEMO00000001",
        location="SYNTHETIC_LOCATION-DEMO0001",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
    )

    for field in REQUIRED_FIELDS:
        assert field in demo_row, f"missing required field {field!r}"
        assert type(demo_row[field]) is type(real_row[field]), (
            f"{field!r} type mismatch: demo={type(demo_row[field])!r} "
            f"real={type(real_row[field])!r}"
        )


def test_build_row_optional_response_status_code_is_a_string_like_the_real_wire():
    real_row = _real_row()
    demo_row = build_row(
        monitor_id="HTTP_CHECK-DEMO00000001",
        location="SYNTHETIC_LOCATION-DEMO0001",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        response_status_code=200,
    )

    assert "result.statistics.response_status_code" in demo_row
    assert type(demo_row["result.statistics.response_status_code"]) is type(
        real_row["result.statistics.response_status_code"]
    )


def test_build_row_duration_is_emitted_as_a_nanosecond_string_not_a_millisecond_string():
    """AC2: the fixture's `"755000000"` is nanoseconds (`_assembly.py:92`
    divides by 1_000_000). Emitting `"755"` (milliseconds) is the SAME type
    (str) and would silently yield `latency_ms == 0` fleet-wide — so this
    asserts the exact wire value, not just the type.
    """
    demo_row = build_row(
        monitor_id="HTTP_CHECK-DEMO00000001",
        location="SYNTHETIC_LOCATION-DEMO0001",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        duration_ms=755,
    )

    assert demo_row["result.statistics.duration"] == "755000000"


def test_build_row_duration_round_trips_through_the_real_assembler_at_755ms():
    """AC2's scale-sane round trip, through the REAL production assembler."""
    from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row

    demo_row = build_row(
        monitor_id="HTTP_CHECK-DEMO00000001",
        location="SYNTHETIC_LOCATION-DEMO0001",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        duration_ms=755,
        response_status_code=200,
    )

    observation = normalize_http_row(demo_row, signal_key="demo-signal")

    assert observation.latency_ms == 755
    assert observation.response_status_code == 200


def test_format_ns_timestamp_matches_the_real_wire_shape():
    from datetime import datetime

    from demo_engine.rows import format_ns_timestamp

    dt = datetime(2026, 6, 29, 8, 30, 40, 746000, tzinfo=timezone.utc)
    assert format_ns_timestamp(dt) == "2026-06-29T08:30:40.746000000Z"
