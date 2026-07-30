"""STORY-148 AC8 & STORY-177 — provisional status code mapping.

`map_synthetic_status` (`health_mapping.py`) maps `code == "0"` / `message == "HEALTHY"` -> `Health.UP`
and provisional pairs `("1", "UNHEALTHY")` -> `Health.DOWN` and `("2", "DEGRADED")` -> `Health.DEGRADED`.

This test verifies that the provisional failure code `ASSUMED_DOWN_CODE` / `ASSUMED_DOWN_MESSAGE`
maps to `Health.DOWN` via `normalize_http_row` and emits a loud warning log (STORY-177).
"""

import logging

import pytest
from demo_engine.assumed_failure_codes import (
    ASSUMED_DEGRADED_CODE,
    ASSUMED_DEGRADED_MESSAGE,
    ASSUMED_DOWN_CODE,
    ASSUMED_DOWN_MESSAGE,
    UNMAPPED_POISON_CODE,
    UNMAPPED_POISON_MESSAGE,
)
from demo_engine.rows import build_row
from src.adapters.inbound.dynatrace.health_mapping import (
    PROVISIONAL_STATUS_MAPPING,
    UnknownVendorStatusError,
)
from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row
from src.core.domain import Health


def test_assumed_failure_code_row_echoes_the_status_code_and_message_given():
    """STORY-180 AC5 (minor 4): renamed from
    `..._produces_a_structurally_valid_row`, which overstated what this test
    asserts -- only that the two status values passed in echo back unchanged,
    not that the row is otherwise "structurally valid" in any broader sense.
    """
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


def test_assumed_failure_code_is_mapped_to_health_down_with_warning(caplog):
    """STORY-177: verifies the assumed failure pair maps to Health.DOWN and logs a warning."""
    row = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        status_code=ASSUMED_DOWN_CODE,
        status_message=ASSUMED_DOWN_MESSAGE,
    )

    with caplog.at_level(
        logging.WARNING, logger="src.adapters.inbound.dynatrace.health_mapping"
    ):
        obs = normalize_http_row(row, signal_key="demo-signal")

    assert obs.health is Health.DOWN
    assert any(
        "Provisional status mapping hit" in r.getMessage() for r in caplog.records
    )


def test_assumed_degraded_code_is_mapped_to_health_degraded_with_warning(caplog):
    """STORY-177 AC1: DEGRADED must reach the domain through the REAL ingest path.

    The DOWN half of the provisional mapping was already covered above; without
    this, AC1's "a DOWN *and a DEGRADED* observation" was only half asserted and
    the second provisional entry could have been wrong (or absent) unnoticed.
    """
    row = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        status_code=ASSUMED_DEGRADED_CODE,
        status_message=ASSUMED_DEGRADED_MESSAGE,
    )

    with caplog.at_level(
        logging.WARNING, logger="src.adapters.inbound.dynatrace.health_mapping"
    ):
        obs = normalize_http_row(row, signal_key="demo-signal")

    assert obs.health is Health.DEGRADED
    assert any(
        "Provisional status mapping hit" in r.getMessage() for r in caplog.records
    )


def test_poison_pair_is_not_in_the_provisional_mapping():
    """The poison pair's ONLY value is being unmapped -- pin that (STORY-191 AC5).

    `UNMAPPED_POISON_*` exists so the poison-row scenario can prove STORY-190's
    quarantine on a real run. That works only while `map_synthetic_status`
    RAISES on it. Nothing in `scenario.py` or the scenario YAML can enforce
    that -- the property lives in ANOTHER module, so adding "999" to
    `PROVISIONAL_STATUS_MAPPING` would silently turn the poison row into an
    ordinary mapped row and STORY-191 AC5 would keep passing while testing
    NOTHING. This test is the pin.
    """
    assert (
        UNMAPPED_POISON_CODE,
        UNMAPPED_POISON_MESSAGE,
    ) not in PROVISIONAL_STATUS_MAPPING

    row = build_row(
        monitor_id="MON-A",
        location="LOC-1",
        event_id="1",
        timestamp="2026-07-29T10:00:00.000000000Z",
        status_code=UNMAPPED_POISON_CODE,
        status_message=UNMAPPED_POISON_MESSAGE,
    )
    with pytest.raises(UnknownVendorStatusError):
        normalize_http_row(row, signal_key="demo-signal")
