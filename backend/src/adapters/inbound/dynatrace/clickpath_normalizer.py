"""Browser-clickpath synthetic monitor normalizer (dossier §5, §7).

Flattens ONE Dynatrace DQL row for a browser-clickpath (`BROWSER_CLICKPATH`)
synthetic monitor execution into the canonical `SignalObservation`. A
clickpath row carries a multi-step journey (`steps`), but the canonical
shape never models step detail (dossier §5 normalization rules, AC3) — this
normalizer reads only the monitor-level `execution.outcome` that Dynatrace
already collapsed the steps into, and ignores the `steps` array entirely.
The raw row (steps included) is what an archived `raw_ref` would point at;
the core never reads it.
"""

from datetime import datetime

from src.core.domain import Provenance, SignalObservation

from src.adapters.inbound.dynatrace.health_mapping import map_execution_outcome

NATIVE_KIND = "clickpath"


def normalize_clickpath_row(
    row: dict, *, signal_key: str, raw_ref: str | None = None
) -> SignalObservation:
    """Normalize one clickpath synthetic-execution DQL row into a `SignalObservation`.

    `row` is the flat dict shape documented in dossier §8 / the recorded
    fixtures (`backend/tests/fixtures/dynatrace/clickpath_multi_location.json`):
    `timestamp`, `event.id`, `synthetic_test.id`, `synthetic_location.name`,
    `execution.outcome` (the monitor-level verdict Dynatrace already collapsed
    the per-step results into), `request.response_time_ms`, and a `steps`
    array that this normalizer deliberately does not read — step detail is
    not modelled on the canonical shape (dossier §5; AC3).
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
        raw_ref=raw_ref,
    )
