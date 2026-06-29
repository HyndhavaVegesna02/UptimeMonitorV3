"""HTTP synthetic monitor normalizer (dossier §5, §7).

Flattens ONE Dynatrace DQL row for an HTTP (`HTTP_CHECK`) synthetic monitor
execution into the canonical `SignalObservation`. One row is one location
execution; this function never aggregates across rows (dossier §5
normalization rules) — the caller (the adapter dispatch, see `adapter.py`)
is responsible for iterating rows.
"""

from src.adapters.inbound.dynatrace._assembly import (
    assemble_observation,
    require_field,
)
from src.adapters.inbound.dynatrace.health_mapping import map_synthetic_status
from src.core.domain import SignalObservation

NATIVE_KIND = "http"


def normalize_http_row(row: dict, *, signal_key: str) -> SignalObservation:
    """Normalize one HTTP synthetic-execution DQL row into a `SignalObservation` (STORY-016b)."""
    code = str(require_field(row, "result.status.code"))
    message = str(require_field(row, "result.status.message"))
    health = map_synthetic_status(code=code, message=message)

    return assemble_observation(
        row,
        signal_key=signal_key,
        health=health,
        native_kind=NATIVE_KIND,
    )
