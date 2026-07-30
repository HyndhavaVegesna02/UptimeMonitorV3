"""STORY-182 AC3 evidence-extraction helpers.

Two deliberately SEPARATE functions for two deliberately DIFFERENT location
field shapes (the B6 trap, SPIKE-064): a raw Grail-shaped demo row carries
the location under `dt.entity.synthetic_location`
(`demo_engine/rows.py:85`) -- NOT `dt.synthetic.location.id`, which is the
shape of the unrelated MONITOR id field (`dt.synthetic.monitor.id`) and the
obvious wrong guess; the API's `ObservationDTO` carries it under a plain
`"location"` key (`api/v1/history/models.py:30`), a third shape again.
Guessing the wrong key does not raise -- it silently reads a `{None}` set
(one "location") and makes AC3 look unreachable while the underlying data is
entirely correct, which is exactly what happened on SPIKE-064's own first
run. Naming two functions, each reading exactly one field, closes that
class of mistake instead of relying on a caller remembering the right key.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def distinct_locations_from_raw_rows(rows: Iterable[Mapping[str, object]]) -> int:
    """Count DISTINCT locations over raw Grail-shaped rows (or the demo
    engine's in-memory equivalent), reading `dt.entity.synthetic_location`
    (`demo_engine/rows.py:85`) -- never `dt.synthetic.location.id`, the
    monitor-id field's shape."""
    return len({row.get("dt.entity.synthetic_location") for row in rows})


def distinct_locations_from_history_dtos(
    observations: Iterable[Mapping[str, object]],
) -> int:
    """Count DISTINCT locations over `GET /api/v1/history`'s JSON response
    (a list of `ObservationDTO`-shaped mappings), reading the plain
    `"location"` field (`api/v1/history/models.py:30`)."""
    return len({obs.get("location") for obs in observations})
