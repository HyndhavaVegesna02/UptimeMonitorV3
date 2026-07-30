"""STORY-182 AC3 evidence-extraction helpers.

The B6 trap (SPIKE-064): a raw Grail-shaped demo row carries the location
under `dt.entity.synthetic_location` (`demo_engine/rows.py:85`) -- NOT
`dt.synthetic.location.id`, which is the shape of the unrelated MONITOR id
field (`dt.synthetic.monitor.id`) and the obvious wrong guess; the API's
`ObservationDTO` carries it under a plain `"location"` key
(`api/v1/history/models.py:30`), a different shape again. Guessing the
wrong key does not raise -- it silently reads a `{None}` set (one
"location") and makes AC3 look unreachable while the underlying data is
entirely correct, which is exactly what happened on SPIKE-064's own first
run.

(STORY-182 fix round minor: this module previously named a SECOND function,
`distinct_locations_from_raw_rows`, reading the raw-row shape above -- but
`harness.py` only ever reads the API's `/history` JSON, never raw Grail
rows directly, so that function had no caller anywhere. Removed rather than
kept as unexercised dead code; the raw-row field shape and the trap it
guards against are still recorded here for the same reason SPIKE-064
originally separated the two.)
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping


def distinct_locations_from_history_dtos(
    observations: Iterable[Mapping[str, object]],
) -> int:
    """Count DISTINCT locations over `GET /api/v1/history`'s JSON response
    (a list of `ObservationDTO`-shaped mappings), reading the plain
    `"location"` field (`api/v1/history/models.py:30`)."""
    return len({obs.get("location") for obs in observations})
