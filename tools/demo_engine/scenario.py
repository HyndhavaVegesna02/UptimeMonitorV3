"""The scenario player — expands a per-signal, per-cycle, per-location
outcome declaration into Grail-shaped demo rows (STORY-176 AC1/AC2).

A scenario file is NOT a random generator (dossier context, STORY-176): it
declares, per signal, an ordered sequence of CYCLES, and each cycle names what
each location reported that cycle. A location omitted from a cycle is simply
ABSENT for that cycle.

**A cycle entry takes one of two shapes** (STORY-191 widened this):

- a LIST of location ids — every one reported `UP`. This is the original
  STORY-176 shape and is unchanged, so every scenario authored against it
  keeps working;
- a MAPPING of location id -> outcome, drawn from the CLOSED vocabulary in
  `_STATUS_MAP` below (`up` / `down` / `degraded` / `poison`).

**Until STORY-177 this engine could emit `UP` and absence ONLY**, because
`map_synthetic_status` raised on every non-healthy code, so "absent" was the
only non-`UP` outcome expressible. STORY-177 landed a provisional mapping and
that is no longer true — `down` and `degraded` now travel the real ingest path.
They remain UNVERIFIED ASSUMPTIONS about vendor codes, never confirmed
contracts (`assumed_failure_codes.py`): a real Dynatrace failure code has still
never been observed.

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

from demo_engine.assumed_failure_codes import (
    ASSUMED_DEGRADED_CODE,
    ASSUMED_DEGRADED_MESSAGE,
    ASSUMED_DOWN_CODE,
    ASSUMED_DOWN_MESSAGE,
    UNMAPPED_POISON_CODE,
    UNMAPPED_POISON_MESSAGE,
)
from demo_engine.rows import (
    STATUS_CODE_HEALTHY,
    STATUS_MESSAGE_HEALTHY,
    build_row,
    format_ns_timestamp,
)


class InvalidScenarioError(ValueError):
    """Raised when a scenario file/block is missing a required field (STORY-176 AC1)."""


@dataclass(frozen=True)
class SignalScenario:
    """One signal's scripted, per-cycle, per-location outcome sequence (STORY-176 AC1, STORY-191).

    `cycles` is ordered OLDEST to NEWEST — `cycles[-1]` is the cycle that
    lands at `expand_scenario`'s `end_time`. Each entry is either a list of
    location native ids reporting `UP` (the original STORY-176 shape), or a
    mapping of location native id -> outcome drawn from the CLOSED vocabulary
    in `_STATUS_MAP`. There is deliberately no free-form "custom" form; see
    that constant for why.
    """

    signal_key: str
    monitor_id: str
    interval_seconds: int
    cycles: list[list[str] | dict[str, str]]

    def __post_init__(self) -> None:
        """Enforce `interval_seconds` is a positive `int` on the TYPE itself
        (STORY-184 AC1/AC2), so NO construction path -- direct or via
        `load_scenario_file` -- can produce a player whose past-anchored
        `expand_scenario` would emit a row after `end_time`.

        `type(...) is not int` (NOT `isinstance`) is deliberate and must not be
        "simplified": `bool` is an `int` subclass in Python, so
        `isinstance(True, int)` is `True` and would silently accept
        `interval_seconds: true` from a YAML file, whereas `type(True) is int`
        is `False`. In-repo precedent for this exact field:
        `composition/config.py::_require_positive_interval` and
        `core/domain/topology.py::Signal._require_positive_interval_when_set`.

        (This rationale was deleted during the sprint-65 external delivery and
        restored in the quality-review round -- without it the next reader
        "tidies" the check into `isinstance` and re-opens STORY-184.)
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
    """Parse a scenario YAML file into a list of `SignalScenario`s (STORY-176 AC1, STORY-191)."""
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
                f"per-cycle location lists or dicts, got {type(cycles).__name__!r}."
            )
        for cycle_index, cycle in enumerate(cycles):
            if isinstance(cycle, list):
                if not all(isinstance(location, str) for location in cycle):
                    raise InvalidScenarioError(
                        f"{path}: scenario {signal_key!r}: cycles[{cycle_index}] "
                        f"must be a list of location id strings or dict, got {cycle!r}."
                    )
            elif isinstance(cycle, dict):
                if not all(
                    isinstance(k, str) and isinstance(v, str) for k, v in cycle.items()
                ):
                    raise InvalidScenarioError(
                        f"{path}: scenario {signal_key!r}: cycles[{cycle_index}] "
                        f"must be a dict mapping location id string to status string, got {cycle!r}."
                    )
                # Vocabulary is checked HERE, at load time, not left to
                # `_resolve_status` at expand time. A typo (`dwon`) otherwise
                # loads clean and surfaces much later as a bare `ValueError`
                # carrying neither the file nor the signal key -- breaking this
                # module's filename-prefixed convention and defeating callers
                # that deliberately pre-load scenarios to fail fast (e.g.
                # `failure_path_reality_gate.py`, which pre-loads precisely so a
                # bad file fails in seconds rather than ~40 minutes into a live
                # loop run). `_resolve_status` keeps its own check as
                # defence-in-depth for directly-constructed SignalScenarios.
                for location, status_str in cycle.items():
                    if status_str.lower() not in _STATUS_MAP:
                        allowed = ", ".join(sorted(_STATUS_MAP))
                        raise InvalidScenarioError(
                            f"{path}: scenario {signal_key!r}: cycles[{cycle_index}] "
                            f"location {location!r} declares unknown outcome "
                            f"{status_str!r}; allowed: {allowed}."
                        )
            else:
                raise InvalidScenarioError(
                    f"{path}: scenario {signal_key!r}: cycles[{cycle_index}] "
                    f"must be a list of location id strings or dict, got {cycle!r}."
                )

        try:
            scenario = SignalScenario(
                signal_key=signal_key,
                monitor_id=monitor_id,
                interval_seconds=interval_seconds,
                cycles=[list(c) if isinstance(c, list) else dict(c) for c in cycles],
            )
        except ValueError as exc:
            raise InvalidScenarioError(
                f"{path}: scenario {signal_key!r}: {exc}"
            ) from exc
        scenarios.append(scenario)
    return scenarios


#: The CLOSED per-location outcome vocabulary a scenario cycle may declare.
#:
#: Every pair is DERIVED from `assumed_failure_codes`, never written literally
#: here — STORY-177 AC2 requires the provisional code literals to exist in
#: exactly ONE place (`health_mapping.PROVISIONAL_STATUS_MAPPING`), so that
#: STORY-154 can replace them without hunting. A hardcoded `("2", "DEGRADED")`
#: in this file would silently break that guarantee.
#:
#: Deliberately CLOSED: there is no free-form `"code:message"` escape hatch.
#: One was briefly present and is removed on purpose — it let any scenario YAML
#: introduce arbitrary vendor literals, which is exactly the single-source rule
#: above defeated by the back door, and it would have let a scenario invent a
#: vendor code that reads as a contract. A genuinely new outcome is a change to
#: the provisional mapping (a reviewed decision), not a string in a fixture.
_STATUS_MAP: dict[str, tuple[str, str]] = {
    "up": (STATUS_CODE_HEALTHY, STATUS_MESSAGE_HEALTHY),
    "down": (ASSUMED_DOWN_CODE, ASSUMED_DOWN_MESSAGE),
    "degraded": (ASSUMED_DEGRADED_CODE, ASSUMED_DEGRADED_MESSAGE),
    # Deliberately UNMAPPED -- `map_synthetic_status` RAISES on it. Used to
    # prove STORY-190's quarantine on a real run (STORY-191 AC5).
    "poison": (UNMAPPED_POISON_CODE, UNMAPPED_POISON_MESSAGE),
}


def _resolve_status(status_str: str) -> tuple[str, str]:
    """Resolve a declared outcome word to its `(code, message)` pair.

    Raises on anything outside the closed vocabulary, naming what IS allowed --
    a scenario typo must fail loudly at load time rather than silently
    expanding to rows nobody asked for.
    """
    try:
        return _STATUS_MAP[status_str.lower()]
    except KeyError:
        allowed = ", ".join(sorted(_STATUS_MAP))
        raise ValueError(
            f"unknown per-location outcome {status_str!r}; allowed: {allowed}"
        ) from None


def expand_scenario(
    scenario: SignalScenario,
    *,
    end_time: datetime,
    event_id_prefix: str | None = None,
) -> list[dict]:
    """Expand one `SignalScenario` into Grail-shaped rows, PAST-ANCHORED (STORY-176 AC2, STORY-191)."""
    interval = timedelta(seconds=scenario.interval_seconds)
    n_cycles = len(scenario.cycles)
    rows: list[dict] = []
    event_seq = 0
    prefix = event_id_prefix if event_id_prefix is not None else scenario.signal_key

    for cycle_index, cycle in enumerate(scenario.cycles):
        cycles_before_end = (n_cycles - 1) - cycle_index
        cycle_time = end_time - cycles_before_end * interval
        timestamp = format_ns_timestamp(cycle_time)
        if isinstance(cycle, list):
            for location in cycle:
                event_seq += 1
                rows.append(
                    build_row(
                        monitor_id=scenario.monitor_id,
                        location=location,
                        event_id=f"{prefix}-{event_seq}",
                        timestamp=timestamp,
                    )
                )
        elif isinstance(cycle, dict):
            for location, status_str in cycle.items():
                event_seq += 1
                code, msg = _resolve_status(status_str)
                rows.append(
                    build_row(
                        monitor_id=scenario.monitor_id,
                        location=location,
                        event_id=f"{prefix}-{event_seq}",
                        timestamp=timestamp,
                        status_code=code,
                        status_message=msg,
                    )
                )

    return rows
