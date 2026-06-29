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


class MalformedDqlRowError(ValueError):
    """Raised when a DQL row is missing a required field (STORY-016b).

    Required fields (`timestamp`, `event.id`, `dt.synthetic.monitor.id`,
    `event.type`, `dt.entity.synthetic_location`) are subscripted
    directly rather than guessed at, so a vendor shape change surfaces as
    this named error naming the missing field instead of a bare `KeyError`.
    `result.statistics.duration` (-> optional `latency_ms`) is read via
    `.get` and stays optional.
    """


def require_field(row: dict, field: str):
    """Read a required DQL row field, raising `MalformedDqlRowError` if absent (STORY-020)."""
    try:
        return row[field]
    except KeyError:
        raise MalformedDqlRowError(
            f"DQL row missing required field: {field!r}"
        ) from None


def parse_ns_timestamp(ts: str) -> datetime:
    """Parse a nanosecond-precision ISO-8601 timestamp safely (STORY-016b).

    Truncates fractional seconds to 6 digits (microseconds) before calling
    `datetime.fromisoformat`.
    """
    s = ts.replace("Z", "+00:00")
    if "." in s:
        main_part, frac_part = s.split(".", 1)
        tz_start = 0
        for i, char in enumerate(frac_part):
            if not char.isdigit():
                tz_start = i
                break
        else:
            tz_start = len(frac_part)

        frac_digits = frac_part[:tz_start]
        tz_part = frac_part[tz_start:]

        # Keep at most 6 digits for microseconds
        frac_digits = frac_digits[:6]
        s = f"{main_part}.{frac_digits}{tz_part}"

    return datetime.fromisoformat(s)


def assemble_observation(
    row: dict,
    *,
    signal_key: str,
    health: Health,
    native_kind: str,
    raw_ref: str | None = None,
) -> SignalObservation:
    """Flatten one real DQL row + an already-computed `Health` into a `SignalObservation` (dossier §5).

    Maps the real Grail fields: `timestamp`, `event.id`, `dt.synthetic.monitor.id`,
    `dt.entity.synthetic_location`, and `result.statistics.duration`.
    """
    observed_at = parse_ns_timestamp(require_field(row, "timestamp"))

    duration_val = row.get("result.statistics.duration")
    latency_ms = None
    if duration_val is not None:
        try:
            latency_ms = int(duration_val) // 1_000_000
        except (ValueError, TypeError):
            pass

    return SignalObservation(
        signal_key=signal_key,
        observed_at=observed_at,
        health=health,
        source_event_id=str(require_field(row, "event.id")),
        source=Provenance(
            system="dynatrace",
            native_id=require_field(row, "dt.synthetic.monitor.id"),
            native_kind=native_kind,
        ),
        location=require_field(row, "dt.entity.synthetic_location"),
        latency_ms=latency_ms,
        raw_ref=raw_ref,
    )
