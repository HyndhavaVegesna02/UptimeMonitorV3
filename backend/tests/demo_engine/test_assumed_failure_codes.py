"""STORY-148 AC8 — assumptions labelled, not buried.

`map_synthetic_status` (`health_mapping.py:54-70`) maps ONLY `code == "0"` /
`message == "HEALTHY"` and RAISES on everything else — its own docstring
states inventing a failure code "would silently mis-map (or mask) the real
failure value during that verification, so it is deliberately NOT done".

This test proves the honest state of affairs: the demo engine CAN build a
failure-shaped row (the wire contract supports emitting one), but the REAL,
unmodified `map_synthetic_status` still raises on it. The assumed code is
therefore exactly that — an assumption, never a verified vendor contract —
and this story does not add a failure mapping to `backend/src/` to make it
"work" (that is STORY-177's first-class decision, not a demo side effect).
"""

import pytest
from demo_engine.assumed_failure_codes import (
    ASSUMED_DOWN_CODE,
    ASSUMED_DOWN_MESSAGE,
)
from demo_engine.rows import build_row
from src.adapters.inbound.dynatrace.health_mapping import UnknownVendorStatusError
from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row


def test_assumed_failure_code_produces_a_structurally_valid_row():
    row = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        status_code=ASSUMED_DOWN_CODE,
        status_message=ASSUMED_DOWN_MESSAGE,
    )

    assert row["result.status.code"] == ASSUMED_DOWN_CODE
    assert row["result.status.message"] == ASSUMED_DOWN_MESSAGE


def test_assumed_failure_code_is_rejected_by_the_real_unmodified_health_mapping():
    row = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        status_code=ASSUMED_DOWN_CODE,
        status_message=ASSUMED_DOWN_MESSAGE,
    )

    with pytest.raises(UnknownVendorStatusError):
        normalize_http_row(row, signal_key="demo-signal")
