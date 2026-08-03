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
  (d) interval — `test_demo_fleet_config.py` covers fleet-authoring (every
      demo signal's declared `interval_seconds`); THIS file covers player
      BEHAVIOUR directly (sprint-63 fix round, quality finding C1): consecutive
      expanded cycles must be spaced by exactly `scenario.interval_seconds`,
      parametrized over more than one interval, so a mutant that ignores the
      field and hardcodes one interval cannot pass both parametrizations;
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


# --- STORY-184: the interval invariant lives on SignalScenario itself ------
#
# STORY-176's fix round (sprint 63) validated interval_seconds only in
# `load_scenario_file` -- direct construction bypassed it entirely, and
# `expand_scenario` (past-anchored) would emit a row AFTER `end_time` for a
# non-positive interval. These tests pin the invariant on the frozen type
# itself, so no construction path -- direct or via the loader -- can produce
# a player that expands into the future.


@pytest.mark.parametrize("interval_seconds", [-30, 0])
def test_signal_scenario_rejects_non_positive_interval_seconds(interval_seconds):
    with pytest.raises(ValueError, match="positive"):
        SignalScenario(
            signal_key="demo-signal",
            monitor_id="HTTP_CHECK-DEMO-TEST",
            interval_seconds=interval_seconds,
            cycles=[["L1"], ["L1"]],
        )


def test_signal_scenario_accepts_a_valid_positive_interval_seconds():
    scenario = SignalScenario(
        signal_key="demo-signal",
        monitor_id="HTTP_CHECK-DEMO-TEST",
        interval_seconds=30,
        cycles=[["L1"]],
    )
    assert scenario.interval_seconds == 30


@pytest.mark.parametrize("bad_value", ["30", 30.5, True])
def test_signal_scenario_rejects_non_int_interval_seconds(bad_value):
    """`bool` is an `int` subclass in Python, so a naive `isinstance(x, int)`
    check would silently accept `True` -- this parametrization is the one
    that pins that case, currently unpinned even at the loader (AC2)."""
    with pytest.raises(ValueError, match="int"):
        SignalScenario(
            signal_key="demo-signal",
            monitor_id="HTTP_CHECK-DEMO-TEST",
            interval_seconds=bad_value,
            cycles=[["L1"]],
        )


def test_signal_scenario_negative_interval_can_no_longer_expand_into_the_future():
    """AC5 -- the previously-reachable future-row outcome. Before this story,
    `SignalScenario(interval_seconds=-30, cycles=[["L1"], ["L1"]])` followed
    by `expand_scenario(scenario, end_time=...)` produced a row at
    `end_time + 30s` -- 30 seconds INTO THE FUTURE relative to `end_time`
    (the exact reproduction the story's Context section verified at HEAD).
    The type invariant now makes the CONSTRUCTION itself raise, so that
    future row is unreachable regardless of whether `expand_scenario` is
    ever called. This is the assertion that failed before this story."""
    with pytest.raises(ValueError):
        SignalScenario(
            signal_key="demo-signal",
            monitor_id="HTTP_CHECK-DEMO-TEST",
            interval_seconds=-30,
            cycles=[["L1"], ["L1"]],
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
        len(group) for _, group in sorted(by_timestamp.items(), key=lambda kv: kv[0])
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
    assert len(set(timestamps)) == len(timestamps), (
        "each cycle must land at a distinct instant"
    )


# --- AC2(d): interval spacing, from the rows themselves ----------------------


@pytest.mark.parametrize("interval_seconds", [30, 45])
def test_expand_scenario_consecutive_cycles_are_spaced_by_the_scenarios_own_interval(
    interval_seconds,
):
    """AC2(d) (sprint-63 fix round, quality finding C1): the gap between
    consecutive expanded cycles must be EXACTLY `scenario.interval_seconds`
    -- driven from the real `expand_scenario`, not a value the test computes
    independently. Parametrized over two distinct intervals so a mutant that
    hardcodes one interval (e.g. always 30s) fails at least one case."""
    scenario = _scenario(
        cycles=[["L1"], ["L1"], ["L1"], ["L1"]], interval_seconds=interval_seconds
    )
    rows = expand_scenario(scenario, end_time=_END)

    timestamps = sorted(parse_ns_timestamp(row["timestamp"]) for row in rows)
    assert len(timestamps) == 4  # one per cycle -- one location, four cycles

    gaps = {b - a for a, b in zip(timestamps, timestamps[1:])}
    assert gaps == {timedelta(seconds=interval_seconds)}


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
    `VENDOR_HEALTH_WINDOW`, mirroring
    `adapters/inbound/dynatrace/query.py`'s `_HEALTH_CHECK_WINDOW`, both
    2h) — so `check_vendor_id_health`'s count
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


# --- Type/sign validation (sprint-63 fix round, quality finding M2) ---------
#
# `load_scenario_file` previously validated only FIELD PRESENCE, not type or
# sign, so a malformed value leaked a bare stdlib exception (`TypeError`) with
# no filename and no signal name -- and a negative `interval_seconds` was not
# rejected at all, which would make `expand_scenario` emit rows in the
# FUTURE (falsifying AC2f). Each case below must raise the NAMED
# `InvalidScenarioError`, carrying both the file path and the signal key.


def test_load_scenario_file_null_cycles_rejected_with_named_error(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: HTTP_CHECK-DEMO-X\n"
        "  interval_seconds: 30\n"
        "  cycles:\n",  # parses to None, not a list
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal") as exc_info:
        load_scenario_file(path)
    assert str(path) in str(exc_info.value)


def test_load_scenario_file_cycles_wrong_type_rejected_with_named_error(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: HTTP_CHECK-DEMO-X\n"
        "  interval_seconds: 30\n"
        "  cycles: 5\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal") as exc_info:
        load_scenario_file(path)
    assert str(path) in str(exc_info.value)


def test_load_scenario_file_cycle_entry_wrong_type_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: HTTP_CHECK-DEMO-X\n"
        "  interval_seconds: 30\n"
        "  cycles:\n"
        "    - L1\n",  # a bare string, not a list of locations
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal"):
        load_scenario_file(path)


def test_load_scenario_file_interval_seconds_string_rejected_with_named_error(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: HTTP_CHECK-DEMO-X\n"
        "  interval_seconds: '30'\n"  # a string, not an int
        "  cycles:\n"
        "    - [L1]\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal") as exc_info:
        load_scenario_file(path)
    assert str(path) in str(exc_info.value)


def test_load_scenario_file_interval_seconds_negative_rejected_with_named_error(
    tmp_path,
):
    """The reproduced defect: a negative `interval_seconds` was previously
    accepted and made `expand_scenario` emit rows in the FUTURE relative to
    `end_time` -- falsifying AC2f. Must be rejected at load time instead."""
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: HTTP_CHECK-DEMO-X\n"
        "  interval_seconds: -30\n"
        "  cycles:\n"
        "    - [L1]\n"
        "    - [L1]\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal") as exc_info:
        load_scenario_file(path)
    assert str(path) in str(exc_info.value)


def test_load_scenario_file_interval_seconds_zero_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: HTTP_CHECK-DEMO-X\n"
        "  interval_seconds: 0\n"
        "  cycles:\n"
        "    - [L1]\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal"):
        load_scenario_file(path)


def test_load_scenario_file_monitor_id_wrong_type_rejected(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        "demo-signal:\n"
        "  monitor_id: 12345\n"  # not a string
        "  interval_seconds: 30\n"
        "  cycles:\n"
        "    - [L1]\n",
        encoding="utf-8",
    )
    with pytest.raises(InvalidScenarioError, match="demo-signal"):
        load_scenario_file(path)
