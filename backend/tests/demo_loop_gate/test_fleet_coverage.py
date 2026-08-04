"""Tests for the STORY-182 fleet-wide coverage artifact (B1).

`config/demo/scenarios/*.yaml` covers only 6 of the demo fleet's 41 signals
(STORY-176 AC5) -- deliberately, since those five scenarios exist to exercise
specific cases (a dark location, a dark monitor, staggered intervals, a late
return), not fleet-wide breadth. STORY-182's AC3/AC4 need EVERY signal to
carry >=1 row inside the trailing 2h vendor-health window
(`adapters/inbound/dynatrace/query.py:136,155`; relocated there from
`composition/vendor_health.py:37,50` at STORY-204), so this module builds a
SEPARATE, fleet-wide artifact via the BUILDER route: construct one `SignalScenario`
per configured signal directly IN CODE from the loaded `Config` (rather than
authoring a second checked-in YAML file) and expand it with the real
`demo_engine.scenario.expand_scenario`.

The builder route is why STORY-184 (the `interval_seconds` type/sign
invariant on `SignalScenario` itself) had to land first in sprint 64: this is
exactly the direct-construction path that invariant guards.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from demo_loop_gate.fleet_coverage import (
    DEFAULT_COVERAGE_CYCLES,
    build_fleet_coverage_scenarios,
    build_fleet_row_store,
)
from src.composition.config import load_config

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEMO_CONFIG_DIR = _REPO_ROOT / "config" / "demo"

_END = datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc)


def _demo_config():
    return load_config(_DEMO_CONFIG_DIR)


def test_build_fleet_coverage_scenarios_covers_every_signal_exactly_once():
    cfg = _demo_config()
    all_signal_keys = {sig.signal_key for app in cfg.apps for sig in app.signals}
    assert len(all_signal_keys) >= 40  # STORY-176 AC4's own floor, re-asserted

    scenarios = build_fleet_coverage_scenarios(cfg)

    scenario_keys = [s.signal_key for s in scenarios]
    assert len(scenario_keys) == len(all_signal_keys)
    assert set(scenario_keys) == all_signal_keys


def test_build_fleet_coverage_scenarios_agree_with_config_on_monitor_id_and_interval():
    cfg = _demo_config()
    scenarios = {s.signal_key: s for s in build_fleet_coverage_scenarios(cfg)}

    for app in cfg.apps:
        for sig in app.signals:
            scenario = scenarios[sig.signal_key]
            assert scenario.monitor_id == sig.native_id
            assert scenario.interval_seconds == sig.interval_seconds


def test_build_fleet_coverage_scenarios_use_every_declared_location_every_cycle():
    cfg = _demo_config()
    scenarios = {s.signal_key: s for s in build_fleet_coverage_scenarios(cfg)}

    for app in cfg.apps:
        declared_native_ids = {
            loc.native_id for loc in cfg.locations_for(app.id).values()
        }
        assert len(declared_native_ids) == 4
        for sig in app.signals:
            scenario = scenarios[sig.signal_key]
            assert len(scenario.cycles) == DEFAULT_COVERAGE_CYCLES
            for cycle in scenario.cycles:
                assert set(cycle) == declared_native_ids


def test_build_fleet_row_store_yields_exact_row_count():
    cfg = _demo_config()
    all_signal_keys = {sig.signal_key for app in cfg.apps for sig in app.signals}

    store = build_fleet_row_store(cfg, end_time=_END)

    # signals x cycles x locations-per-signal(4), exact -- not a >= bound, so
    # a builder that silently drops a signal or a location is caught here.
    assert len(store._rows) == len(all_signal_keys) * DEFAULT_COVERAGE_CYCLES * 4


def test_build_fleet_row_store_rows_are_inside_the_trailing_2h_window_and_never_future():
    cfg = _demo_config()
    store = build_fleet_row_store(cfg, end_time=_END)

    from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp

    timestamps = [parse_ns_timestamp(row["timestamp"]) for row in store._rows]
    assert timestamps, "expected at least one row"
    assert all(ts <= _END for ts in timestamps)
    assert all(ts >= _END - timedelta(hours=2) for ts in timestamps)
