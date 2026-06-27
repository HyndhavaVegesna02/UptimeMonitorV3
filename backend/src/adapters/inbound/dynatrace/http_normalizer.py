"""HTTP synthetic monitor normalizer (dossier §5, §7).

Flattens ONE Dynatrace DQL row for an HTTP (`HTTP_CHECK`) synthetic monitor
execution into the canonical `SignalObservation`. One row is one location
execution; this function never aggregates across rows (dossier §5
normalization rules) — the caller (the adapter dispatch, see `adapter.py`)
is responsible for iterating rows.
"""

from src.adapters.inbound.dynatrace._assembly import assemble_observation
from src.adapters.inbound.dynatrace.health_mapping import map_execution_outcome
from src.core.domain import SignalObservation

NATIVE_KIND = "http"


def normalize_http_row(row: dict, *, signal_key: str) -> SignalObservation:
    """Normalize one HTTP synthetic-execution DQL row into a `SignalObservation`.

    `row` is the flat dict shape documented in dossier §8 / the recorded
    fixtures (`backend/tests/fixtures/dynatrace/http_multi_location.json`):
    `timestamp`, `event.id`, `synthetic_test.id`, `synthetic_location.name`,
    `execution.outcome`, and `request.response_time_ms`. The timestamp parse
    and `SignalObservation`/`Provenance` assembly are shared with the
    clickpath normalizer via `_assembly.assemble_observation`; only the health
    mapping (a single vendor outcome here) is HTTP-specific.
    """
    return assemble_observation(
        row,
        signal_key=signal_key,
        health=map_execution_outcome(row["execution.outcome"]),
        native_kind=NATIVE_KIND,
    )
