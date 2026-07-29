"""Tests for the scenario player (STORY-176 AC1, AC2).

AC1: a scenario file declares per-signal, per-cycle, per-location outcomes,
and the player expands it into rows at each monitor's own `interval_seconds`
— a declared sequence produces EXACTLY the expected row count per location
per cycle.

AC2: the time base's four (really six, per the sprint-63 plan-verifier
finding) constraints, each asserted independently:
  (a) window — the rolling 7-cycle window `orchestrate.py:94-98` computes;
  (b) format — 9-digit-fraction, `Z`-suffixed UTC, matching the real fixture;
  (c) monotonicity — timestamps advance across successive cycles;
  (d) interval — covered in `test_demo_fleet_config.py` (fleet-authoring, not
      player behaviour);
  (e) backfill — the last row lands at (or before) `end_time`, trivially
      inside the vendor-health engine's 2h window;
  (f) not in the future — no row's timestamp exceeds `end_time`.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

import pytest
from demo_engine.scenario import (
    InvalidScenarioError,
    SignalScenario,
    expand_scenario,
    load_scenario_file,
)
from demo_engine.store import VENDOR_HEALTH_WINDOW
from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp
from src.core.services.pipeline import AntiFlapThresholds

_END = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{9}Z$")


def _scenario(cycles: list[list[str]], interval_seconds: int = 30) -> SignalScenario:
    return SignalScenario(
        signal_key="demo-signal",
        monitor_id="HTTP_CHECK-DEMO-TEST",
        interval_seconds=interval_seconds,
        cycles=cycles,
    )


# --- AC1: row count per location per cycle ---------------------------------


def test_expand_scenario_produces_exact_row_count_per_location_per_cycle():
    scenario = _scenario(
        cycles=[
            ["L1", "L2", "L3"],
            ["L1", "L2", "L3"],
            [],  # a fully dark cycle
            ["L1", "L2"],
        ]
    )

    rows = expand_scenario(scenario, end_time=_END)

    assert len(rows) == 3 + 3 + 0 + 2

    # Group by timestamp (one per cycle, since cycles are `interval_seconds`
    # apart) and check the row count landing in each cycle, in order.
    by_timestamp: dict[str, list[dict]] = {}
    for row in rows:
        by_timestamp.setdefault(row["timestamp"], []).append(row)
    counts_in_cycle_order = [
        len(group)
        for _, group in sorted(by_timestamp.items(), key=lambda kv: kv[0])
    ]
    # Oldest to newest: cycle 0 (3 locations), cycle 1 (3 locations), cycle 2
    # (empty — contributes no timestamp group at all), cycle 3 (2 locations).
    assert counts_in_cycle_order == [3, 3, 2]


def test_expand_scenario_empty_cycles_list_produces_no_rows():
    scenario = _scenario(cycles=[])
    assert expand_scenario(scenario, end_time=_END) == []


def test_expand_scenario_row_locations_match_declared_locations_for_that_cycle():
    scenario = _scenario(cycles=[["L1", "L2"], ["L1"]])
    rows = expand_scenario(scenario, end_time=_END)
    locations = sorted(row["dt.entity.synthetic_location"] for row in rows)
    assert locations == ["L1", "L1", "L2"]


# --- AC2(b): format ----------------------------------------------------------


def test_expand_scenario_timestamps_are_9_digit_fraction_z_suffixed_utc():
    scenario = _scenario(cycles=[["L1"], ["L1"]])
    rows = expand_scenario(scenario, end_time=_END)

    for row in rows:
        assert _TIMESTAMP_RE.match(row["timestamp"]), row["timestamp"]
        # Must round-trip through the REAL production parser (signal.py
        # rejects naive/non-UTC — `parse_ns_timestamp` is what the ingest
        # path actually uses).
        parsed = parse_ns_timestamp(row["timestamp"])
        assert parsed.tzinfo is not None
        assert parsed.utcoffset() == timedelta(0)


# --- AC2(c): monotonicity ----------------------------------------------------


def test_expand_scenario_timestamps_advance_across_successive_cycles():
    scenario = _scenario(cycles=[["L1"], ["L1"], ["L1"], ["L1"], ["L1"]])
    rows = expand_scenario(scenario, end_time=_END)

    timestamps = [parse_ns_timestamp(row["timestamp"]) for row in rows]
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) == len(timestamps), "each cycle must land at a distinct instant"


# --- AC2(f): never in the future --------------------------------------------


def test_expand_scenario_no_row_lands_after_end_time():
    scenario = _scenario(cycles=[["L1", "L2"], ["L1", "L2"], ["L1", "L2"]])
    rows = expand_scenario(scenario, end_time=_END)

    for row in rows:
        assert parse_ns_timestamp(row["timestamp"]) <= _END


def test_expand_scenario_last_cycle_lands_exactly_at_end_time():
    scenario = _scenario(cycles=[["L1"], ["L1"], ["L1"]])
    rows = expand_scenario(scenario, end_time=_END)

    latest = max(parse_ns_timestamp(row["timestamp"]) for row in rows)
    assert latest == _END


# --- AC2(e): backfill relative to the request instant -----------------------


def test_expand_scenario_last_row_is_within_the_vendor_health_window():
    """AC2(e): the engine serves history relative to the REQUEST instant, not
    "since engine start". Because expansion is past-anchored to `end_time`,
    the most recent row is always at (or before) `end_time` — trivially
    inside the vendor-health engine's trailing window (`store.py`'s
    `VENDOR_HEALTH_WINDOW`, mirroring `vendor_health.py`'s
    `_HEALTH_CHECK_WINDOW`, both 2h) — so `check_vendor_id_health`'s count
    probe never sees a dead-looking monitor id the instant the scenario is
    expanded (STORY-176 AC2e; the plan-verifier's over-specification note —
    only >=1 row inside the trailing window is required, not dense history)."""
    scenario = _scenario(cycles=[["L1"], ["L1"], ["L1"]])
    rows = expand_scenario(scenario, end_time=_END)

    latest = max(parse_ns_timestamp(row["timestamp"]) for row in rows)
    assert _END - latest < VENDOR_HEALTH_WINDOW


# --- AC2(a): the rolling 7-cycle window --------------------------------------


def test_expand_scenario_ladder_fits_inside_orchestrates_rolling_window():
    """AC2(a): `orchestrate.py:94-98` computes
    `since = until - (max_threshold + 2) * interval` — a rolling 7-cycle
    window at the dossier §10 defaults (major=5 -> 5+2=7). A scenario with
    <=7 cycles, past-anchored to `until`, lands entirely inside
    `[since, until]` on the very first query — the whole ladder is visible
    immediately, never waiting on wall-clock time (the past-anchored
    decision this AC exists to pin)."""
    thresholds = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)
    interval_seconds = 30
    interval = timedelta(seconds=interval_seconds)
    until = _END
    max_threshold = max(
        thresholds.major, thresholds.partial, thresholds.degraded, thresholds.recovery
    )
    since = until - (max_threshold + 2) * interval  # 7 cycles

    scenario = _scenario(
        cycles=[["L1"]] * 5, interval_seconds=interval_seconds
    )  # a 5-cycle ladder, inside the 7-cycle window
    rows = expand_scenario(scenario, end_time=until)

    for row in rows:
        ts = parse_ns_timestamp(row["timestamp"])
        assert since <= ts <= until


# --- AC1 file format ----------------------------------------------------------


_SCENARIO_YAML = """\
demo-signal-a:
  monitor_id: HTTP_CHECK-DEMO-A
  interval_seconds: 30
  cycles:
    - [L1, L2]
    - []
    - [L1]
demo-signal-b:
  monitor_id: HTTP_CHECK-DEMO-B
  interval_seconds: 45
  cycles:
    - [L1, L2, L3]
"""


def test_load_scenario_file_parses_multiple_signals(tmp_path):
    path = tmp_path / "scenario.yaml"
    path.write_text(_SCENARIO_YAML, encoding="utf-8")

    scenarios = load_scenario_file(path)

    by_key = {s.signal_key: s for s in scenarios}
    assert set(by_key) == {"demo-signal-a", "demo-signal-b"}
    assert by_key["demo-signal-a"].monitor_id == "HTTP_CHECK-DEMO-A"
    assert by_key["demo-signal-a"].interval_seconds == 30
    assert by_key["demo-signal-a"].cycles == [["L1", "L2"], [], ["L1"]]
    assert by_key["demo-signal-b"].interval_seconds == 45


def test_load_scenario_file_expansion_matches_direct_construction(tmp_path):
    path = tmp_path / "scenario.yaml"
    path.write_text(_SCENARIO_YAML, encoding="utf-8")

    scenarios = load_scenario_file(path)
    by_key = {s.signal_key: s for s in scenarios}
    rows = expand_scenario(by_key["demo-signal-a"], end_time=_END)

    assert len(rows) == 2 + 0 + 1


# --- Empty-input / malformed-input behaviour (checklist 2026-06-25) --------


def test_load_scenario_file_rejects_non_mapping_top_level(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.raises(InvalidScenarioError, match="mapping"):
        load_scenario_file(path)


@pytest.mark.parametrize("missing_field", ["monitor_id", "interval_seconds", "cycles"])
def test_load_scenario_file_missing_required_field_raises(tmp_path, missing_field):
    block = {
        "monitor_id": "HTTP_CHECK-DEMO-X",
        "interval_seconds": 30,
        "cycles": [["L1"]],
    }
    del block[missing_field]
    import yaml

    path = tmp_path / "bad.yaml"
    path.write_text(yaml.safe_dump({"demo-signal": block}), encoding="utf-8")

    with pytest.raises(InvalidScenarioError, match=missing_field):
        load_scenario_file(path)
