"""Tests for STORY-182 AC3 evidence-extraction helpers.

The B6 trap: raw demo rows carry the location under
`dt.entity.synthetic_location` (`demo_engine/rows.py:85`), NOT
`dt.synthetic.location.id` (the shape of the MONITOR id field,
`dt.synthetic.monitor.id`) -- guessing the wrong key silently reads a
`{None}` set, i.e. one "location", and makes AC3 look unreachable while the
data is entirely correct (SPIKE-064's own first run made exactly this
mistake). The API-facing DTOs use a plain `"location"` key
(`api/v1/history/models.py:30`), a THIRD shape again -- so a helper reading
raw Grail rows and a helper reading API JSON responses are deliberately two
different functions, never one guessing across both shapes.
"""

from __future__ import annotations

from demo_loop_gate.evidence import (
    distinct_locations_from_history_dtos,
    distinct_locations_from_raw_rows,
)


def test_distinct_locations_from_raw_rows_reads_the_entity_synthetic_location_field():
    rows = [
        {"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-DEMOA"},
        {"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-DEMOB"},
        {"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-DEMOA"},
    ]
    assert distinct_locations_from_raw_rows(rows) == 2


def test_distinct_locations_from_raw_rows_wrong_key_would_have_silently_collapsed_to_one():
    """Documents the B6 trap directly: reading the MONITOR id shape key
    instead would see every row as the same (missing) value."""
    rows = [
        {"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-DEMOA"},
        {"dt.entity.synthetic_location": "SYNTHETIC_LOCATION-DEMOB"},
    ]
    wrong_key_reading = len({row.get("dt.synthetic.location.id") for row in rows})
    assert wrong_key_reading == 1  # {None} -- looks like exactly one location
    assert distinct_locations_from_raw_rows(rows) == 2  # the real answer


def test_distinct_locations_from_history_dtos_reads_the_location_field():
    observations = [
        {"signal_key": "sig-1", "location": "loc-a"},
        {"signal_key": "sig-1", "location": "loc-b"},
        {"signal_key": "sig-1", "location": "loc-a"},
        {"signal_key": "sig-1", "location": "loc-c"},
    ]
    assert distinct_locations_from_history_dtos(observations) == 3


def test_distinct_locations_from_history_dtos_empty_list_is_zero():
    assert distinct_locations_from_history_dtos([]) == 0


def test_distinct_locations_from_raw_rows_empty_list_is_zero():
    assert distinct_locations_from_raw_rows([]) == 0
