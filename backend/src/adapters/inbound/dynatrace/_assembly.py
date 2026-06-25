"""Shared observation-assembly helper (dossier §5, §7).

Both per-type normalizers (`http_normalizer.py`, `clickpath_normalizer.py`)
flatten one DQL row into a canonical `SignalObservation`, and that assembly —
the `timestamp` parse plus the `SignalObservation`/`Provenance` construction —
is identical across monitor types; only the already-computed `Health` verdict,
the vendor `native_kind`, and (for clickpath) an optional `raw_ref` differ.
This module is the single place that assembly is written, so a future
timestamp-format or field fix lands once instead of drifting between
normalizers. The per-type health verdict (a single outcome for HTTP, a
multi-step collapse for clickpath) stays in each normalizer — this helper only
ever receives the already-computed `Health`.
"""

from datetime import datetime

from src.core.domain import Health, Provenance, SignalObservation


def assemble_observation(
    row: dict,
    *,
    signal_key: str,
    health: Health,
    native_kind: str,
    raw_ref: str | None = None,
) -> SignalObservation:
    """Flatten one DQL row + an already-computed `Health` into a `SignalObservation`.

    `row` is the flat dict shape shared by every monitor type's fixtures:
    `timestamp`, `event.id`, `synthetic_test.id`, `synthetic_location.name`,
    and `request.response_time_ms`. `health` and `native_kind` are supplied by
    the caller (the per-type normalizer), since deriving the verdict from the
    row is per-type logic that does not belong here. `raw_ref` is optional and
    symmetric across both call sites — callers that have no raw payload
    pointer simply omit it.
    """
    observed_at = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))

    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at,
        health=health,
        source_event_id=row["event.id"],
        source=Provenance(
            system="dynatrace",
            native_id=row["synthetic_test.id"],
            native_kind=native_kind,
        ),
        location=row["synthetic_location.name"],
        latency_ms=row.get("request.response_time_ms"),
        raw_ref=raw_ref,
    )
