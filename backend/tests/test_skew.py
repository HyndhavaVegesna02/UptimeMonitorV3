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

from src.core.services.skew import SignalFeeder, SkewResult

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
