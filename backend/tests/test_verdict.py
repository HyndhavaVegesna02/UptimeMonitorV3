"""STORY-010: the `Verdict` canonical domain type (dossier §10, stages 1-2).

Zone 1 / pure core. `Verdict` is the per-cycle output of `collapse` (the input
to `streak`): either a normal health verdict for one signal's cycle, or a
maintenance marker that short-circuits the rest of the pipeline (dossier §10;
V2 FR-8). Tested with in-memory fixtures only — no DB, no vendor types.
"""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.core.domain import Health, Verdict


def _valid_verdict(**overrides):
    """A construction-ready set of valid `Verdict` fields; override to probe a rule."""
    fields = dict(
        signal_key="checkout-http",
        observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=Health.UP,
        under_maintenance=False,
    )
    fields.update(overrides)
    return fields


# --- Step 1: Verdict constructs; frozen (AC1 support type) ----------------------


def test_verdict_constructs_from_valid_fields():
    verdict = Verdict(**_valid_verdict())
    assert verdict.signal_key == "checkout-http"
    assert verdict.observed_at == datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    assert verdict.health is Health.UP
    assert verdict.under_maintenance is False


def test_verdict_is_frozen():
    verdict = Verdict(**_valid_verdict())
    with pytest.raises(ValidationError):
        verdict.health = Health.DOWN


def test_maintenance_verdict_carries_no_health_verdict():
    verdict = Verdict(
        signal_key="checkout-http",
        observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=None,
        under_maintenance=True,
    )
    assert verdict.under_maintenance is True
    assert verdict.health is None


# --- STORY-025: the maintenance<->health invariant is enforced at construction --


def test_normal_verdict_omitting_health_raises():
    """`under_maintenance=False` with `health` left at its `None` default is incoherent.

    Superseded by STORY-025: this combination used to construct fine (`health`
    defaulting to `None`); it is now one of the two invalid shapes the
    `model_validator` rejects.
    """
    fields = _valid_verdict()
    del fields["health"]
    with pytest.raises(ValidationError):
        Verdict(**fields)


def test_maintenance_verdict_with_health_raises():
    with pytest.raises(ValidationError):
        Verdict(
            signal_key="checkout-http",
            observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
            health=Health.UP,
            under_maintenance=True,
        )


def test_normal_verdict_with_explicit_none_health_raises():
    with pytest.raises(ValidationError):
        Verdict(**_valid_verdict(health=None))


def test_normal_verdict_with_set_health_constructs():
    verdict = Verdict(**_valid_verdict(health=Health.DOWN, under_maintenance=False))
    assert verdict.under_maintenance is False
    assert verdict.health is Health.DOWN


def test_maintenance_verdict_with_none_health_constructs():
    verdict = Verdict(
        signal_key="checkout-http",
        observed_at=datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc),
        health=None,
        under_maintenance=True,
    )
    assert verdict.under_maintenance is True
    assert verdict.health is None
