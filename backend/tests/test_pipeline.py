"""STORY-010: core pipeline stages 1-2 — collapse + streak (dossier §10).

Zone 4 / pure core. `collapse` maps one signal's per-location observations for
a cycle to a single `Verdict`; `streak` counts consecutive same-health
verdicts reading backward over non-maintenance verdicts. Tested with
in-memory canonical fixtures only — no DB, no vendor types, no I/O.
"""

from datetime import datetime, timedelta, timezone

import pytest

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


# --- Step 4: maintenance is excluded from the verdict + short-circuits -------


def test_collapse_under_maintenance_excludes_the_verdict_even_when_all_up():
    # Even an all-up cycle yields no up/down verdict once flagged under
    # maintenance: maintenance is planned work, neither up nor down (V2 FR-8).
    observations = [
        _observation(Health.UP, "us-east"),
        _observation(Health.UP, "eu-west"),
    ]
    verdict = collapse(observations, under_maintenance=True)
    assert verdict.under_maintenance is True
    assert verdict.health is None


def test_collapse_under_maintenance_short_circuits_even_when_all_down():
    # A down cycle flagged under maintenance still yields no health verdict —
    # maintenance short-circuits the rest of the pipeline before health is
    # ever considered.
    observations = [
        _observation(Health.DOWN, "us-east"),
        _observation(Health.DOWN, "eu-west"),
    ]
    verdict = collapse(observations, under_maintenance=True)
    assert verdict.under_maintenance is True
    assert verdict.health is None


def test_collapse_under_maintenance_preserves_signal_key_and_cycle_instant():
    observations = [
        _observation(Health.UP, "us-east", offset_seconds=0, signal_key="payments-http"),
        _observation(Health.UP, "eu-west", offset_seconds=30, signal_key="payments-http"),
    ]
    verdict = collapse(observations, under_maintenance=True)
    assert verdict.signal_key == "payments-http"
    assert verdict.observed_at == _BASE_TIME + timedelta(seconds=30)


# --- Step 5: collapse on an empty cycle raises a clear domain error ----------


def test_collapse_raises_clear_domain_error_on_empty_observations():
    # The symmetric case to streak([]) -> None: collapse has no observation to
    # derive a cycle instant or signal key from, so it must fail loudly with a
    # domain-level message rather than leak a stdlib max()/IndexError detail.
    with pytest.raises(ValueError, match="collapse requires at least one observation"):
        collapse([], under_maintenance=False)
