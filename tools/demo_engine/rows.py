"""Grail-shaped demo row builder (STORY-148 AC1, AC2).

Builds rows that are structurally and value-type identical to a real
Dynatrace Grail `http_monitor_execution` row, verified field-by-field against
the real captured sample
`backend/tests/fixtures/dynatrace/grail_synthetic_events.json`
(`backend/tests/demo_engine/test_rows.py`).

Only the fields the real ingest path actually reads are modeled here: the
five the assembler requires (`_assembly.py:86,108,111,114`), the two the
normalizer requires (`http_normalizer.py:22-23`), and the two optional
statistics fields (`_assembly.py:88-102`). Cosmetic fixture fields
(`event.kind`, `result.state`, `dt.entity.http_check`, `monitor.name`, ...)
are deliberately omitted — no production code reads them, and including them
would suggest they matter to the wire contract when they don't.
"""

from __future__ import annotations

from datetime import datetime, timedelta

#: The one live HTTP monitor event type (`query.py:87`); the only type this
#: engine's ingest grammar ever scopes to.
EVENT_TYPE_HTTP_MONITOR_EXECUTION = "http_monitor_execution"

#: The ONLY (code, message) pair `map_synthetic_status` accepts
#: (`health_mapping.py:65`) — real, verified vendor values.
STATUS_CODE_HEALTHY = "0"
STATUS_MESSAGE_HEALTHY = "HEALTHY"


def format_ns_timestamp(dt: datetime) -> str:
    """Format a tz-aware UTC datetime as a 9-digit-fraction Grail timestamp.

    Real Grail rows carry nanosecond precision, e.g. `...746000000Z`
    (fixture:4) — always exactly 9 fractional digits. Python has no
    sub-microsecond precision, so the trailing 3 digits are always `000`,
    matching the real captured sample's own shape (both fixture rows end
    `...000`).
    """
    if dt.tzinfo is None or dt.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be a tz-aware UTC datetime")
    base = dt.strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{dt.microsecond:06d}000Z"


def build_row(
    *,
    monitor_id: str,
    location: str,
    event_id: str,
    timestamp: str,
    event_type: str = EVENT_TYPE_HTTP_MONITOR_EXECUTION,
    status_code: str = STATUS_CODE_HEALTHY,
    status_message: str = STATUS_MESSAGE_HEALTHY,
    duration_ms: int | None = None,
    response_status_code: int | None = None,
) -> dict:
    """Build one Grail-shaped demo row (STORY-148 AC1/AC2).

    `timestamp` is the caller's ISO string, unmodified (use
    `format_ns_timestamp` to produce one matching the real wire's
    nanosecond-precision shape).

    `duration_ms`/`response_status_code` are given in their NATURAL units and
    converted to the real wire's string/nanosecond shape here — a caller
    cannot accidentally repeat the "755" (ms) vs "755000000" (ns) units trap
    STORY-148 AC2 exists to catch, because there is no string-typed
    "duration" parameter to get wrong.

    `status_code`/`status_message` default to the ONE verified healthy pair;
    passing anything else is an ASSUMPTION about an unobserved vendor value
    (STORY-148 AC8) — see `assumed_failure_codes.py`.
    """
    row: dict = {
        "timestamp": timestamp,
        "event.id": event_id,
        "event.type": event_type,
        "dt.synthetic.monitor.id": monitor_id,
        "dt.entity.synthetic_location": location,
        "result.status.code": status_code,
        "result.status.message": status_message,
    }
    if duration_ms is not None:
        row["result.statistics.duration"] = str(duration_ms * 1_000_000)
    if response_status_code is not None:
        row["result.statistics.response_status_code"] = str(response_status_code)
    return row
