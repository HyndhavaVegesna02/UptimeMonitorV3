"""STORY-010: core pipeline stages 1-2 — collapse + streak (dossier §10).

Zone 4 / pure core. `collapse` maps one signal's per-location observations for
a cycle to a single `Verdict`; `streak` counts consecutive same-health
verdicts reading backward over non-maintenance verdicts. Tested with
in-memory canonical fixtures only — no DB, no vendor types, no I/O.
"""

from datetime import datetime, timedelta, timezone

from src.core.domain import Health, Provenance, SignalObservation, Verdict
from src.core.services.pipeline import collapse

_BASE_TIME = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)


def _observation(health: Health, location: str, *, offset_seconds: int = 0, **overrides):
    """A construction-ready `SignalObservation`; override one field to probe a rule."""
    fields = dict(
        signal_key="checkout-http",
        observed_at=_BASE_TIME + timedelta(seconds=offset_seconds),
        health=health,
        source_event_id=f"evt-{location}-{offset_seconds}",
        source=Provenance(system="dynatrace", native_id="HTTP_CHECK-1", native_kind="http"),
        location=location,
    )
    fields.update(overrides)
    return SignalObservation(**fields)


# --- Step 2: collapse -> up when every observation in the cycle is up ----------


def test_collapse_returns_up_for_single_up_observation():
    observations = [_observation(Health.UP, "us-east")]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.UP
    assert verdict.under_maintenance is False


def test_collapse_returns_up_when_all_locations_are_up():
    observations = [
        _observation(Health.UP, "us-east"),
        _observation(Health.UP, "eu-west"),
        _observation(Health.UP, "ap-south"),
    ]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.UP


def test_collapse_preserves_signal_key_on_the_verdict():
    observations = [_observation(Health.UP, "us-east", signal_key="payments-http")]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.signal_key == "payments-http"


# --- Step 3: collapse -> down (all down) / degraded (mixed, any non-up) -------


def test_collapse_returns_down_for_single_down_observation():
    observations = [_observation(Health.DOWN, "us-east")]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.DOWN


def test_collapse_returns_down_when_all_locations_are_down():
    observations = [
        _observation(Health.DOWN, "us-east"),
        _observation(Health.DOWN, "eu-west"),
    ]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.DOWN


def test_collapse_returns_degraded_when_up_and_down_are_mixed():
    observations = [
        _observation(Health.UP, "us-east"),
        _observation(Health.DOWN, "eu-west"),
    ]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.DEGRADED


def test_collapse_returns_degraded_when_up_and_degraded_are_mixed():
    observations = [
        _observation(Health.UP, "us-east"),
        _observation(Health.DEGRADED, "eu-west"),
    ]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.DEGRADED


def test_collapse_returns_degraded_when_all_locations_are_degraded():
    observations = [
        _observation(Health.DEGRADED, "us-east"),
        _observation(Health.DEGRADED, "eu-west"),
    ]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.DEGRADED


def test_collapse_returns_degraded_for_three_way_mix():
    observations = [
        _observation(Health.UP, "us-east"),
        _observation(Health.DOWN, "eu-west"),
        _observation(Health.DEGRADED, "ap-south"),
    ]
    verdict = collapse(observations, under_maintenance=False)
    assert verdict.health is Health.DEGRADED
