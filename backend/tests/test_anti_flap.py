"""STORY-028: anti-flap — stage 3 of the core pipeline (dossier §10).

Zone 4 / pure core. `anti_flap` maps a `Streak` (STORY-010) plus INJECTED
per-app `AntiFlapThresholds` to an `AntiFlapOutcome` — a proposed
`ComponentStatus`, a distinct internal-warning marker (never published), or
nothing. Tested with in-memory canonical fixtures only — no DB, no vendor
types, no I/O, no config read.
"""

from src.core.domain import ComponentStatus, Health
from src.core.services.pipeline import (
    AntiFlapOutcome,
    AntiFlapThresholds,
    Streak,
    anti_flap,
)

# dossier §10 defaults: major=5, partial=3, degraded=2, recovery=2.
_THRESHOLDS = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)


# --- Step 1: the thresholds value object + outcome type construct and are frozen --


def test_thresholds_construct_with_the_dossier_defaults():
    thresholds = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)
    assert thresholds.major == 5
    assert thresholds.partial == 3
    assert thresholds.degraded == 2
    assert thresholds.recovery == 2


def test_thresholds_are_frozen():
    thresholds = AntiFlapThresholds(major=5, partial=3, degraded=2, recovery=2)
    with __import__("pytest").raises(Exception):
        thresholds.major = 10  # type: ignore[misc]


def test_outcome_constructs_with_a_proposed_status():
    outcome = AntiFlapOutcome(proposed_status=ComponentStatus.DEGRADED, internal_warning=False)
    assert outcome.proposed_status is ComponentStatus.DEGRADED
    assert outcome.internal_warning is False


def test_outcome_constructs_as_an_internal_warning():
    outcome = AntiFlapOutcome(proposed_status=None, internal_warning=True)
    assert outcome.proposed_status is None
    assert outcome.internal_warning is True


def test_outcome_constructs_as_nothing():
    outcome = AntiFlapOutcome(proposed_status=None, internal_warning=False)
    assert outcome.proposed_status is None
    assert outcome.internal_warning is False


def test_outcome_is_frozen():
    outcome = AntiFlapOutcome(proposed_status=None, internal_warning=False)
    with __import__("pytest").raises(Exception):
        outcome.internal_warning = True  # type: ignore[misc]
