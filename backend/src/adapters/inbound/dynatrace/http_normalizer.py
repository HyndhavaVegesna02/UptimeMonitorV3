"""HTTP synthetic monitor normalizer (dossier §5, §7).

Flattens ONE Dynatrace DQL row for an HTTP (`HTTP_CHECK`) synthetic monitor
execution into the canonical `SignalObservation`. One row is one location
execution; this function never aggregates across rows (dossier §5
normalization rules) — the caller (the adapter dispatch, see `adapter.py`)
is responsible for iterating rows.
"""

from datetime import datetime

from src.core.domain import Provenance, SignalObservation

from src.adapters.inbound.dynatrace.health_mapping import map_execution_outcome

NATIVE_KIND = "http"


def normalize_http_row(row: dict, *, signal_key: str) -> SignalObservation:
    """Normalize one HTTP synthetic-execution DQL row into a `SignalObservation`.

    `row` is the flat dict shape documented in dossier §8 / the recorded
    fixtures (`backend/tests/fixtures/dynatrace/http_multi_location.json`):
    `timestamp`, `event.id`, `synthetic_test.id`, `synthetic_location.name`,
    `execution.outcome`, and `request.response_time_ms`.
    """
    observed_at = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))

    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at,
        health=map_execution_outcome(row["execution.outcome"]),
        source_event_id=row["event.id"],
        source=Provenance(
            system="dynatrace",
            native_id=row["synthetic_test.id"],
            native_kind=NATIVE_KIND,
        ),
        location=row["synthetic_location.name"],
        latency_ms=row.get("request.response_time_ms"),
    )
