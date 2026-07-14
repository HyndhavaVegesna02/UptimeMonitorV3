from __future__ import annotations

from datetime import datetime, timezone

import pytest
from src.adapters.persistence.dynamo_serde import from_canonical_iso, to_canonical_iso


def test_serialize_utc_with_microseconds():
    dt = datetime(2026, 7, 14, 12, 34, 56, 123456, tzinfo=timezone.utc)
    s = to_canonical_iso(dt)
    assert s == "2026-07-14T12:34:56.123456+00:00"


def test_serialize_utc_without_microseconds():
    dt = datetime(2026, 7, 14, 12, 34, 56, 0, tzinfo=timezone.utc)
    s = to_canonical_iso(dt)
    assert s == "2026-07-14T12:34:56.000000+00:00"


def test_serialize_non_utc_normalizes_to_utc():
    # Offset of +05:30 -> subtracts 5h30m to get UTC
    from datetime import timedelta

    tz = timezone(timedelta(hours=5, minutes=30))
    dt = datetime(2026, 7, 14, 17, 30, 0, 0, tzinfo=tz)
    s = to_canonical_iso(dt)
    assert s == "2026-07-14T12:00:00.000000+00:00"


def test_serialize_rejects_naive():
    dt = datetime(2026, 7, 14, 12, 34, 56)
    with pytest.raises(ValueError, match="Naive datetime not allowed"):
        to_canonical_iso(dt)


def test_parse_canonical():
    s = "2026-07-14T12:34:56.123456+00:00"
    dt = from_canonical_iso(s)
    assert dt == datetime(2026, 7, 14, 12, 34, 56, 123456, tzinfo=timezone.utc)


def test_parse_alternative_formats():
    # If the format is slightly different but represents the same UTC time, it parses back to tz-aware UTC
    s1 = "2026-07-14T12:34:56.123456Z"
    assert from_canonical_iso(s1) == datetime(
        2026, 7, 14, 12, 34, 56, 123456, tzinfo=timezone.utc
    )

    s2 = "2026-07-14T12:34:56Z"
    assert from_canonical_iso(s2) == datetime(
        2026, 7, 14, 12, 34, 56, 0, tzinfo=timezone.utc
    )


def test_lexicographical_order():
    dt1 = datetime(2026, 7, 14, 12, 34, 56, 0, tzinfo=timezone.utc)
    dt2 = datetime(2026, 7, 14, 12, 34, 56, 1, tzinfo=timezone.utc)
    dt3 = datetime(2026, 7, 14, 12, 34, 57, 0, tzinfo=timezone.utc)

    s1 = to_canonical_iso(dt1)
    s2 = to_canonical_iso(dt2)
    s3 = to_canonical_iso(dt3)

    assert s1 < s2 < s3
