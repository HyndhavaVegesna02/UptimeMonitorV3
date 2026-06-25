"""STORY-010: streak — stage 2 of the core pipeline (dossier §10).

Zone 4 / pure core. `streak` counts consecutive same-health verdicts reading
BACKWARD (most recent first) over an ordered sequence of `Verdict`s, skipping
maintenance verdicts entirely (AC2/AC3). Tested with in-memory canonical
fixtures only — no DB, no vendor types, no I/O.
"""

from datetime import datetime, timedelta, timezone

from src.core.domain import Health, Verdict
from src.core.services.pipeline import Streak, streak

_BASE_TIME = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)


def _verdict(health: Health | None, *, offset_minutes: int, under_maintenance: bool = False):
    """A construction-ready `Verdict`; verdicts are passed oldest-to-newest."""
    return Verdict(
        signal_key="checkout-http",
        observed_at=_BASE_TIME + timedelta(minutes=offset_minutes),
        health=health,
        under_maintenance=under_maintenance,
    )


# --- Step 5: streak counts consecutive same-health verdicts, backward --------


def test_streak_of_one_verdict_has_length_one():
    verdicts = [_verdict(Health.UP, offset_minutes=0)]
    result = streak(verdicts)
    assert result == Streak(health=Health.UP, length=1)


def test_streak_counts_consecutive_same_health_verdicts():
    verdicts = [
        _verdict(Health.UP, offset_minutes=0),
        _verdict(Health.UP, offset_minutes=1),
        _verdict(Health.UP, offset_minutes=2),
    ]
    result = streak(verdicts)
    assert result == Streak(health=Health.UP, length=3)


def test_streak_terminates_at_a_health_change_reading_backward():
    verdicts = [
        _verdict(Health.UP, offset_minutes=0),
        _verdict(Health.DOWN, offset_minutes=1),
        _verdict(Health.DOWN, offset_minutes=2),
        _verdict(Health.DOWN, offset_minutes=3),
    ]
    # Most recent health is DOWN; only the trailing run of DOWN counts —
    # the leading UP at minute 0 must not extend the streak.
    result = streak(verdicts)
    assert result == Streak(health=Health.DOWN, length=3)


def test_streak_resets_to_one_after_the_most_recent_change():
    verdicts = [
        _verdict(Health.DOWN, offset_minutes=0),
        _verdict(Health.DOWN, offset_minutes=1),
        _verdict(Health.UP, offset_minutes=2),
    ]
    result = streak(verdicts)
    assert result == Streak(health=Health.UP, length=1)


def test_streak_treats_degraded_as_its_own_health_value():
    verdicts = [
        _verdict(Health.UP, offset_minutes=0),
        _verdict(Health.DEGRADED, offset_minutes=1),
        _verdict(Health.DEGRADED, offset_minutes=2),
    ]
    result = streak(verdicts)
    assert result == Streak(health=Health.DEGRADED, length=2)
