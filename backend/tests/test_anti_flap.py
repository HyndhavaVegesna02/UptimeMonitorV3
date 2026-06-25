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


def _down(length: int) -> Streak:
    return Streak(health=Health.DOWN, length=length)


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


# --- Step 2: a FAILING streak maps to major/partial/degraded by length (AC1, AC4) --


def test_failing_streak_at_major_threshold_proposes_major_outage():
    outcome = anti_flap(_down(_THRESHOLDS.major), _THRESHOLDS)
    assert outcome == AntiFlapOutcome(
        proposed_status=ComponentStatus.MAJOR_OUTAGE, internal_warning=False
    )


def test_failing_streak_above_major_threshold_proposes_major_outage():
    outcome = anti_flap(_down(_THRESHOLDS.major + 1), _THRESHOLDS)
    assert outcome.proposed_status is ComponentStatus.MAJOR_OUTAGE


def test_failing_streak_just_below_major_threshold_proposes_partial_outage():
    # major=5; length 4 clears partial (>=3) but not major.
    outcome = anti_flap(_down(_THRESHOLDS.major - 1), _THRESHOLDS)
    assert outcome == AntiFlapOutcome(
        proposed_status=ComponentStatus.PARTIAL_OUTAGE, internal_warning=False
    )


def test_failing_streak_at_partial_threshold_proposes_partial_outage():
    outcome = anti_flap(_down(_THRESHOLDS.partial), _THRESHOLDS)
    assert outcome == AntiFlapOutcome(
        proposed_status=ComponentStatus.PARTIAL_OUTAGE, internal_warning=False
    )


def test_failing_streak_just_below_partial_threshold_proposes_degraded():
    # partial=3; length 2 clears degraded (>=2) but not partial.
    outcome = anti_flap(_down(_THRESHOLDS.partial - 1), _THRESHOLDS)
    assert outcome == AntiFlapOutcome(
        proposed_status=ComponentStatus.DEGRADED, internal_warning=False
    )


def test_failing_streak_at_degraded_threshold_proposes_degraded():
    outcome = anti_flap(_down(_THRESHOLDS.degraded), _THRESHOLDS)
    assert outcome == AntiFlapOutcome(
        proposed_status=ComponentStatus.DEGRADED, internal_warning=False
    )


def test_failing_severity_ladder_is_checked_most_severe_first():
    # A pathological-but-legal thresholds object where partial == degraded:
    # a streak that also clears major must still win major, not fall through
    # to a lower rung — the ladder is order-sensitive, most-severe-first.
    thresholds = AntiFlapThresholds(major=3, partial=3, degraded=3, recovery=2)
    outcome = anti_flap(_down(3), thresholds)
    assert outcome.proposed_status is ComponentStatus.MAJOR_OUTAGE


# --- Step 3: a single failure (length 1) is a distinct internal warning (AC2) --


def test_single_failure_below_degraded_threshold_yields_internal_warning():
    outcome = anti_flap(_down(1), _THRESHOLDS)
    assert outcome == AntiFlapOutcome(proposed_status=None, internal_warning=True)


def test_internal_warning_is_never_a_published_component_status():
    # The internal-warning outcome must never carry a proposed_status — it is
    # a distinct, unpublishable signal, not a quiet alias for "degraded" or
    # any other ComponentStatus.
    outcome = anti_flap(_down(1), _THRESHOLDS)
    assert outcome.proposed_status is None
    assert outcome.internal_warning is True


def test_internal_warning_still_applies_when_degraded_threshold_is_one():
    # If an app's degraded threshold is configured down to 1, a single
    # failure clears it via the ladder ("length >= degraded") and proposes
    # degraded — the internal-warning rung only applies when length 1 is
    # genuinely BELOW the degraded threshold, never as a separate override.
    thresholds = AntiFlapThresholds(major=5, partial=3, degraded=1, recovery=2)
    outcome = anti_flap(_down(1), thresholds)
    assert outcome == AntiFlapOutcome(proposed_status=ComponentStatus.DEGRADED, internal_warning=False)
