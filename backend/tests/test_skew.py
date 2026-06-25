"""STORY-026: the per-component skew flag (dossier §11 "Skew, surfaced", Tier-2 T2.7).

Zone 4 / pure core. `skew` compares a component's feeding signals' watermarks
against each other — a feeder is SKEWED when it lags the most-recent peer
watermark by MORE than its own `interval`. Distinct from `AvailabilityResult`
(AC2): rides alongside completeness but is never derived from it. Tested with
IN-MEMORY fixtures only — no DB, no topology load, no vendor types, no I/O.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from src.core.services.skew import SignalFeeder, SkewResult, skew

_NOW = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)
_INTERVAL = timedelta(minutes=5)


def _feeder(signal_key: str, watermark: datetime | None, *, interval: timedelta = _INTERVAL) -> SignalFeeder:
    return SignalFeeder(signal_key=signal_key, watermark=watermark, interval=interval)


# --- Step 1: the feeder input shape + SkewResult construct and are frozen ---


def test_signal_feeder_constructs_with_all_fields():
    feeder = SignalFeeder(signal_key="checkout-http", watermark=_NOW, interval=_INTERVAL)

    assert feeder.signal_key == "checkout-http"
    assert feeder.watermark == _NOW
    assert feeder.interval == _INTERVAL


def test_signal_feeder_allows_a_none_watermark():
    # AC4: a signal that has never advanced has no watermark yet.
    feeder = SignalFeeder(signal_key="checkout-http", watermark=None, interval=_INTERVAL)

    assert feeder.watermark is None


def test_signal_feeder_is_frozen():
    feeder = SignalFeeder(signal_key="checkout-http", watermark=_NOW, interval=_INTERVAL)

    with pytest.raises(ValidationError):
        feeder.watermark = None  # type: ignore[misc]


def test_skew_result_constructs_with_skewed_and_lagging_signals():
    result = SkewResult(skewed=True, lagging_signals=("checkout-http",))

    assert result.skewed is True
    assert result.lagging_signals == ("checkout-http",)


def test_skew_result_constructs_as_not_skewed_with_no_lagging_signals():
    result = SkewResult(skewed=False, lagging_signals=())

    assert result.skewed is False
    assert result.lagging_signals == ()


def test_skew_result_is_frozen():
    result = SkewResult(skewed=False, lagging_signals=())

    with pytest.raises(ValidationError):
        result.skewed = True  # type: ignore[misc]


# --- Step 2: a feeder lagging more than its interval is flagged (AC1, AC4) --
#
# Reference = the most-recent peer watermark (the MAX across all feeders).
# A feeder is skewed when reference - feeder.watermark > feeder.interval.
# Lagging by EXACTLY the interval is NOT skewed (">" not ">="), per the
# sprint-7 boundary-value agreement.


def test_feeder_lagging_more_than_its_interval_is_flagged_skewed():
    feeders = [
        _feeder("fresh", _NOW),
        _feeder("stale", _NOW - timedelta(minutes=6)),  # 6m lag > 5m interval
    ]

    result = skew(feeders)

    assert result.skewed is True
    assert result.lagging_signals == ("stale",)


def test_feeder_within_its_interval_is_not_flagged():
    feeders = [
        _feeder("fresh", _NOW),
        _feeder("slightly-behind", _NOW - timedelta(minutes=3)),  # 3m lag < 5m interval
    ]

    result = skew(feeders)

    assert result.skewed is False
    assert result.lagging_signals == ()


def test_feeder_lagging_exactly_its_interval_is_not_skewed():
    # Boundary: lag == interval is NOT skewed ("> ", not ">=").
    feeders = [
        _feeder("fresh", _NOW),
        _feeder("at-boundary", _NOW - _INTERVAL),  # exactly 5m lag == 5m interval
    ]

    result = skew(feeders)

    assert result.skewed is False
    assert result.lagging_signals == ()


def test_feeder_lagging_just_over_its_interval_is_skewed():
    # Boundary: lag == interval + 1 second IS skewed.
    feeders = [
        _feeder("fresh", _NOW),
        _feeder("just-over", _NOW - _INTERVAL - timedelta(seconds=1)),
    ]

    result = skew(feeders)

    assert result.skewed is True
    assert result.lagging_signals == ("just-over",)


def test_multiple_lagging_feeders_are_all_named():
    feeders = [
        _feeder("fresh", _NOW),
        _feeder("stale-1", _NOW - timedelta(minutes=10)),
        _feeder("stale-2", _NOW - timedelta(minutes=20)),
    ]

    result = skew(feeders)

    assert result.skewed is True
    assert result.lagging_signals == ("stale-1", "stale-2")


def test_the_freshest_feeder_itself_is_never_flagged():
    # The feeder supplying the reference watermark (lag == 0) cannot be
    # skewed relative to itself.
    feeders = [
        _feeder("freshest", _NOW),
        _feeder("also-fresh", _NOW),
    ]

    result = skew(feeders)

    assert result.skewed is False
    assert result.lagging_signals == ()


def test_each_feeders_own_interval_governs_its_own_lag_tolerance():
    # Two feeders lag the reference by the same 6 minutes, but only the one
    # with the tighter (5m) interval is skewed; the other's looser (10m)
    # interval tolerates the same lag.
    feeders = [
        _feeder("fresh", _NOW),
        _feeder("tight-interval", _NOW - timedelta(minutes=6), interval=timedelta(minutes=5)),
        _feeder("loose-interval", _NOW - timedelta(minutes=6), interval=timedelta(minutes=10)),
    ]

    result = skew(feeders)

    assert result.skewed is True
    assert result.lagging_signals == ("tight-interval",)
