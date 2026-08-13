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

from src.adapters.inbound.dynatrace._assembly import (
    assemble_observation,
    require_field,
)
from src.adapters.inbound.dynatrace.health_mapping import map_execution_outcome
from src.core.domain import SignalObservation

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
    not modelled on the canonical shape (dossier §5; AC3). The timestamp parse
    and `SignalObservation`/`Provenance` assembly are shared with the HTTP
    normalizer via `_assembly.assemble_observation`; only the health mapping
    (the multi-step-to-one-verdict collapse) is clickpath-specific.
    """
    return assemble_observation(
        row,
        signal_key=signal_key,
        health=map_execution_outcome(require_field(row, "execution.outcome")),
        native_kind=NATIVE_KIND,
        raw_ref=raw_ref,
    )
