"""Assumed (UNVERIFIED) vendor failure codes for the demo engine (STORY-148 AC8, STORY-177).

`map_synthetic_status` (`adapters/inbound/dynatrace/health_mapping.py`)
maps `("1", "UNHEALTHY")` -> `Health.DOWN` and `("2", "DEGRADED")` -> `Health.DEGRADED`
via `PROVISIONAL_STATUS_MAPPING` (STORY-177).

These codes are provisional assumptions pending live Dynatrace trial renewal (STORY-154),
imported directly from `src.adapters.inbound.dynatrace.health_mapping`.
See `tools/demo_engine/README.md`.
"""

from __future__ import annotations

from src.adapters.inbound.dynatrace.health_mapping import PROVISIONAL_STATUS_MAPPING

# Extract the DOWN pair from PROVISIONAL_STATUS_MAPPING (C1 zone rule: tools/ imports backend/src/)
_down_pair = next(
    pair for pair, health in PROVISIONAL_STATUS_MAPPING.items() if health.name == "DOWN"
)

ASSUMED_DOWN_CODE = _down_pair[0]
ASSUMED_DOWN_MESSAGE = _down_pair[1]

