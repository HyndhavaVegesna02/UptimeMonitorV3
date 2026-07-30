"""The fleet-wide coverage artifact (STORY-182 B1).

`config/demo/scenarios/*.yaml` (STORY-176 AC5) covers only 6 of the demo
fleet's 41 signals -- by design, since those five files exist to exercise
specific cases, not fleet-wide breadth. An unseeded monitor id returns `[]`
from `demo_engine.store.DemoRowStore` (`store.py:59-72`), so every uncovered
signal both ingests nothing AND drifts `check_vendor_id_health`
(`composition/vendor_health.py:96-97,113`) -- STORY-182's AC3/AC4 are
unreachable through the five existing scenarios alone.

This module is the fix, via the BUILDER route (chosen over a checked-in
`whole-fleet.yaml`, per the sprint-64 plan's "implementer's call, stated with
its reason"): construct one `SignalScenario` PER CONFIGURED SIGNAL directly
from the loaded `Config`, deriving `monitor_id`/`interval_seconds` from the
signal itself and the cycle locations from the signal's OWN app's declared
`locations:` block (`Config.locations_for`) -- rather than duplicating those
values in a second YAML file that could silently drift from `config/demo`.
This is also why STORY-184 (the `interval_seconds` type/sign invariant moved
onto `SignalScenario.__post_init__` itself) had to land before this story:
constructing `SignalScenario` in code is exactly the path that invariant
guards.

Only 5 cycles are used, not ~2h of ladder: `check_vendor_id_health` needs
>=1 row inside the trailing 2h window (`vendor_health.py:37,50`), not 2h of
coverage -- confirmed empirically by SPIKE-064 (820 rows, 0 drift warnings,
41 health-OK lines). The literal "2h of coverage" reading would cost ~39,000
rows for no additional benefit.
"""

from __future__ import annotations

from datetime import datetime

from demo_engine.scenario import SignalScenario, expand_scenario
from demo_engine.store import DemoRowStore
from src.composition.config import Config

#: 5 cycles is sufficient (SPIKE-064): the vendor-health probe only needs
#: >=1 row inside its trailing 2h window, and this repo's demo intervals
#: (30/45/60s) put 5 cycles comfortably inside that window with room to
#: spare -- never "2h of coverage" (~39,000 rows for the whole fleet).
DEFAULT_COVERAGE_CYCLES = 5


def build_fleet_coverage_scenarios(
    config: Config, *, cycles: int = DEFAULT_COVERAGE_CYCLES
) -> list[SignalScenario]:
    """Construct one `SignalScenario` per configured signal (STORY-182 B1).

    Every cycle reports `UP` from every location declared in that signal's
    OWN app (`Config.locations_for(app.id)`) -- this repo's demo fleet
    declares the SAME 4 locations on every app (confirmed at source,
    SPIKE-064), so this also satisfies AC3's ">=4 locations" per signal.
    """
    scenarios: list[SignalScenario] = []
    for app in config.apps:
        location_native_ids = [
            loc.native_id for loc in config.locations_for(app.id).values()
        ]
        for signal in app.signals:
            scenarios.append(
                SignalScenario(
                    signal_key=signal.signal_key,
                    monitor_id=signal.native_id,
                    interval_seconds=signal.interval_seconds,
                    cycles=[list(location_native_ids) for _ in range(cycles)],
                )
            )
    return scenarios


def build_fleet_row_store(
    config: Config,
    *,
    end_time: datetime,
    cycles: int = DEFAULT_COVERAGE_CYCLES,
) -> DemoRowStore:
    """Expand every fleet-wide `SignalScenario` into ONE shared `DemoRowStore`.

    Past-anchored on `end_time` (`demo_engine.scenario.expand_scenario`'s own
    contract): every row lands at or before `end_time`, and the oldest row is
    `(cycles - 1) * interval_seconds` before it -- comfortably inside the
    vendor-health probe's trailing 2h window for every signal in this fleet
    (intervals are 30/45/60s).
    """
    store = DemoRowStore()
    for scenario in build_fleet_coverage_scenarios(config, cycles=cycles):
        for row in expand_scenario(scenario, end_time=end_time):
            store.add_row(row)
    return store
