"""DynamoDB serialization and deserialization utility."""

from __future__ import annotations

from datetime import datetime, timezone


def to_canonical_iso(dt: datetime) -> str:
    """Serialize a tz-aware datetime to canonical ISO UTC format:
    YYYY-MM-DDTHH:MM:SS.ffffff+00:00
    Naive datetimes are rejected with ValueError.
    """
    if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
        raise ValueError("Naive datetime not allowed")

    # Normalize to UTC
    utc_dt = dt.astimezone(timezone.utc)
    # Format with microseconds and explicit +00:00 offset
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+00:00"


def from_canonical_iso(s: str) -> datetime:
    """Parse a canonical ISO UTC format back to a tz-aware UTC datetime."""
    # datetime.fromisoformat parses timezone offsets like +00:00 or Z
    parsed = datetime.fromisoformat(s)
    if parsed.tzinfo is None:
        raise ValueError("Parsed datetime lacks timezone info")
    return parsed.astimezone(timezone.utc)
