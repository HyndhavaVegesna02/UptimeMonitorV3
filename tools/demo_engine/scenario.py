"""The scenario player — expands a per-signal, per-cycle, per-location
outcome declaration into Grail-shaped demo rows (STORY-176 AC1/AC2).

A scenario file is NOT a random generator (dossier context, STORY-176): it
declares, per signal, an ordered sequence of CYCLES, and each cycle names
exactly which locations report `UP` that cycle. A location omitted from a
cycle's list is simply ABSENT for that cycle — this engine emits `UP` and
absence only (`assumed_failure_codes.py`; a real vendor failure code has
never been observed), so "absent" is the only non-`UP` outcome a scenario can
express.

**Past-anchored expansion (STORY-176 AC2, decided at planning).** `end_time`
(typically `clock.now()`) is where the LAST declared cycle lands; earlier
cycles are placed successively further back at the monitor's own
`interval_seconds`. Expanding backwards from "now" rather than forwards from
a fixed start means the WHOLE declared ladder is inside the ingest window on
the very first query, regardless of how long ago the scenario file was
authored — a forward player would need wall-clock time to pass to fill in
cycles beyond `end_time`, and (STORY-176 AC2f) every cycle beyond
`end_time + 5min` would be silently quarantined by
`ingest_service.py::FUTURE_TOLERANCE` in the meantime.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from demo_engine.rows import build_row, format_ns_timestamp


class InvalidScenarioError(ValueError):
    """Raised when a scenario file/block is missing a required field (STORY-176 AC1)."""


@dataclass(frozen=True)
class SignalScenario:
    """One signal's scripted, per-cycle, per-location outcome sequence (STORY-176 AC1).

    `cycles` is ordered OLDEST to NEWEST — `cycles[-1]` is the cycle that
    lands at `expand_scenario`'s `end_time`. Each entry is the list of
    location native ids reporting `UP` that cycle; a location's absence from
    the list means it did not report at all that cycle (this engine has no
    other outcome to express — see the module docstring).
    """

    signal_key: str
    monitor_id: str
    interval_seconds: int
    cycles: list[list[str]]

    def __post_init__(self) -> None:
        """Enforce `interval_seconds` is a positive `int` on the TYPE itself
        (STORY-184 AC1/AC2), so no construction path -- direct or via
        `load_scenario_file` -- can produce a player whose past-anchored
        `expand_scenario` would emit a row after `end_time`. `type(...) is
        not int` (not `isinstance`) is deliberate: `bool` is an `int`
        subclass in Python, so `isinstance(True, int)` is `True` and would
        silently accept it; `type(True) is int` is `False`. In-repo
        precedent for this exact field: `composition/config.py
        ::_require_positive_interval` and
        `core/domain/topology.py::Signal._require_positive_interval_when_set`.
        """
        if type(self.interval_seconds) is not int:
            raise ValueError(
                "interval_seconds must be an int, got "
                f"{type(self.interval_seconds).__name__!r} "
                f"({self.interval_seconds!r})."
            )
        if self.interval_seconds <= 0:
            raise ValueError(
                "interval_seconds must be positive, got "
                f"{self.interval_seconds!r} -- expand_scenario is "
                "past-anchored, so a non-positive interval would emit rows "
                "in the future."
            )


def load_scenario_file(path: str | Path) -> list[SignalScenario]:
    """Parse a scenario YAML file into a list of `SignalScenario`s (STORY-176 AC1).

    Shape (top-level mapping, one entry per signal)::

        api-gateway-health:
          monitor_id: HTTP_CHECK-DEMO-APIGW-HEALTH
          interval_seconds: 30
          cycles:
            - [SYNTHETIC_LOCATION-DEMOA, SYNTHETIC_LOCATION-DEMOB]
            - []               # a fully dark cycle
            - [SYNTHETIC_LOCATION-DEMOA, SYNTHETIC_LOCATION-DEMOB]

    Raises `InvalidScenarioError` when a signal block is missing
    `monitor_id`, `interval_seconds`, or `cycles` — a malformed scenario file
    must surface loudly rather than silently expand to zero rows. Also
    raises `InvalidScenarioError` (never a bare stdlib `TypeError`) when a
    present field has the wrong TYPE, or when `interval_seconds` is not
    strictly positive — `expand_scenario` is past-anchored (module
    docstring), so a non-positive interval would emit rows in the FUTURE
    relative to `end_time` (STORY-176 AC2f). Every raised message names both
    the file (`path`) and the offending signal key, matching the
    filename-prefixed convention `composition/config.py::load_config` uses
    for its own per-file/per-entry errors.

    `interval_seconds`'s type/sign check itself lives on `SignalScenario.
    __post_init__` (STORY-184), not here — this function catches the bare
    `ValueError` it raises and re-raises it as an `InvalidScenarioError`
    prefixed with the file path and signal key, which the type itself has no
    way to know.
    """
    raw: Any = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise InvalidScenarioError(
            f"Expected a YAML mapping at the top level of {path!r}, "
            f"got {type(raw).__name__!r}."
        )

    scenarios: list[SignalScenario] = []
    for signal_key, block in raw.items():
        if not isinstance(block, dict):
            raise InvalidScenarioError(
                f"{path}: scenario block for {signal_key!r} must be a "
                f"mapping, got {type(block).__name__!r}."
            )
        for field in ("monitor_id", "interval_seconds", "cycles"):
            if field not in block:
                raise InvalidScenarioError(
                    f"{path}: scenario block for {signal_key!r} is missing "
                    f"required field {field!r}."
                )

        monitor_id = block["monitor_id"]
        if not isinstance(monitor_id, str):
            raise InvalidScenarioError(
                f"{path}: scenario {signal_key!r}: monitor_id must be a "
                f"string, got {type(monitor_id).__name__!r}."
            )

        interval_seconds = block["interval_seconds"]

        cycles = block["cycles"]
        if not isinstance(cycles, list):
            raise InvalidScenarioError(
                f"{path}: scenario {signal_key!r}: cycles must be a list of "
                f"per-cycle location lists, got {type(cycles).__name__!r}."
            )
        for cycle_index, cycle in enumerate(cycles):
            if not isinstance(cycle, list) or not all(
                isinstance(location, str) for location in cycle
            ):
                raise InvalidScenarioError(
                    f"{path}: scenario {signal_key!r}: cycles[{cycle_index}] "
                    f"must be a list of location id strings, got {cycle!r}."
                )

        try:
            scenario = SignalScenario(
                signal_key=signal_key,
                monitor_id=monitor_id,
                interval_seconds=interval_seconds,
                cycles=[list(cycle) for cycle in cycles],
            )
        except ValueError as exc:
            # `SignalScenario.__post_init__` (STORY-184) already validated
            # everything else above; the only invariant it can still raise
            # here is interval_seconds's type/sign, since it has no
            # knowledge of `path`. Re-raise with that context attached.
            raise InvalidScenarioError(f"{path}: scenario {signal_key!r}: {exc}") from exc
        scenarios.append(scenario)
    return scenarios


def expand_scenario(
    scenario: SignalScenario,
    *,
    end_time: datetime,
) -> list[dict]:
    """Expand one `SignalScenario` into Grail-shaped rows, PAST-ANCHORED (STORY-176 AC2).

    `scenario.cycles[-1]` lands at `end_time`; `scenario.cycles[-2]` lands one
    `interval_seconds` earlier, and so on — the whole ladder sits at or
    before `end_time`, never after (AC2f: never in the future). Rows are
    built via `demo_engine.rows.build_row`, so they carry exactly the seven
    Grail fields the real ingest path reads, formatted via
    `format_ns_timestamp` (AC2b: the 9-digit-fraction `Z`-suffixed shape).

    An empty `cycles` list (a signal declared but never expanded) or an empty
    per-cycle location list (a fully dark cycle) both produce zero rows for
    that cycle — never an error; "no data that cycle" is a valid, common
    scenario outcome (AC5b/c/e).
    """
    interval = timedelta(seconds=scenario.interval_seconds)
    n_cycles = len(scenario.cycles)
    rows: list[dict] = []
    event_seq = 0

    for cycle_index, locations in enumerate(scenario.cycles):
        cycles_before_end = (n_cycles - 1) - cycle_index
        cycle_time = end_time - cycles_before_end * interval
        timestamp = format_ns_timestamp(cycle_time)
        for location in locations:
            event_seq += 1
            rows.append(
                build_row(
                    monitor_id=scenario.monitor_id,
                    location=location,
                    event_id=f"{scenario.signal_key}-{event_seq}",
                    timestamp=timestamp,
                )
            )

    return rows
