"""STORY-011: the availability engine — two-grain math + group rollup (dossier §11).

Zone 4 / pure core. `core/services/availability.py` computes availability%
(over collapsed verdicts) and completeness% (over raw observations) on
demand, plus a group rollup — derive-on-read, nothing persisted. Tested with
IN-MEMORY FAKE repositories only (no DB, no Dynatrace — working agreement).
Reuses `collapse` (STORY-010); never consults the streak (P4).
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.core.domain import Health, Provenance, SignalObservation
from src.core.services.availability import AvailabilityResult, rollup_group

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fakes import FakeObservationRepository  # noqa: E402  (after sys.path setup above)

_COMPUTED_AT = datetime(2026, 6, 25, 12, 0, 0, tzinfo=timezone.utc)
_SINCE = datetime(2026, 6, 25, 10, 0, 0, tzinfo=timezone.utc)
_INTERVAL = timedelta(minutes=5)
_SIGNAL = "checkout-http"


def _observation(
    health: Health,
    location: str,
    *,
    offset: timedelta,
    event_id: str,
) -> SignalObservation:
    return SignalObservation(
        signal_key=_SIGNAL,
        observed_at=_SINCE + offset,
        health=health,
        source_event_id=event_id,
        source=Provenance(system="dynatrace", native_id="HTTP_CHECK-1", native_kind="http"),
        location=location,
    )


def _repo_with(observations: list[SignalObservation]) -> FakeObservationRepository:
    repo = FakeObservationRepository()
    repo.save_new(observations)
    return repo


# --- AvailabilityResult: frozen result shape (dossier §11) -------------------


def test_availability_result_constructs_with_all_frozen_fields():
    result = AvailabilityResult(
        availability_pct=0.5,
        completeness_pct=0.75,
        total_verdicts=4,
        passing_verdicts=2,
        maintenance_verdicts=1,
        gap_verdicts=0,
        distinct_locations=3,
        window="24h",
        computed_at=_COMPUTED_AT,
    )

    assert result.availability_pct == 0.5
    assert result.completeness_pct == 0.75
    assert result.total_verdicts == 4
    assert result.passing_verdicts == 2
    assert result.maintenance_verdicts == 1
    assert result.gap_verdicts == 0
    assert result.distinct_locations == 3
    assert result.window == "24h"
    assert result.computed_at == _COMPUTED_AT


def test_availability_result_is_frozen():
    result = AvailabilityResult(
        availability_pct=1.0,
        completeness_pct=1.0,
        total_verdicts=1,
        passing_verdicts=1,
        maintenance_verdicts=0,
        gap_verdicts=0,
        distinct_locations=1,
        window="24h",
        computed_at=_COMPUTED_AT,
    )

    try:
        result.availability_pct = 0.0  # type: ignore[misc]
    except (TypeError, ValueError) as exc:
        # Pydantic v2 frozen models raise ValidationError (a ValueError
        # subclass); accept either to avoid coupling to the exact type.
        assert "frozen" in str(exc).lower()
    else:
        raise AssertionError("expected assignment to a frozen model to raise")


def test_availability_result_allows_none_percentages():
    # AC6: the empty/degenerate case carries None percentages, not a sentinel
    # like 0.0 or -1, so a caller cannot mistake "no data" for "0% available".
    result = AvailabilityResult(
        availability_pct=None,
        completeness_pct=None,
        total_verdicts=0,
        passing_verdicts=0,
        maintenance_verdicts=0,
        gap_verdicts=0,
        distinct_locations=0,
        window="24h",
        computed_at=_COMPUTED_AT,
    )

    assert result.availability_pct is None
    assert result.completeness_pct is None


# --- AC1: availability% over collapsed verdicts (dossier §11) ---------------
#
# Cycle bucketing: the window [since, until) is sliced into consecutive
# `interval`-wide buckets starting at `since` (bucket k covers
# [since + k*interval, since + (k+1)*interval)). Every observation falls into
# exactly one bucket by its `observed_at`; a bucket with >=1 observation is
# one cycle, collapsed via `collapse` (one signal, one cycle, per its
# contract). A bucket with zero observations is a gap (AC1: excluded from
# the availability denominator under the default `exclude` policy) -- it
# never reaches `collapse`. `maintenance` is an injected predicate over the
# cycle's start instant (mirrors STORY-010's injected `under_maintenance`
# boolean -- never a DB/table lookup), so a whole cycle can be marked under
# maintenance without per-observation flags.


def _calculator(repo):
    from src.core.services.availability import AvailabilityCalculator

    return AvailabilityCalculator(observation_repo=repo)


def test_availability_pct_all_up_cycles_is_one_hundred_percent():
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=5), event_id="e2"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=10), event_id="e3"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=15),
        interval=_INTERVAL,
        window="15m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.availability_pct == 1.0
    assert result.total_verdicts == 3
    assert result.passing_verdicts == 3
    assert result.maintenance_verdicts == 0
    assert result.gap_verdicts == 0


def test_availability_pct_down_and_degraded_cycles_do_not_pass():
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.DOWN, "us-east", offset=timedelta(minutes=5), event_id="e2"),
        _observation(Health.DEGRADED, "us-east", offset=timedelta(minutes=10), event_id="e3"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=15), event_id="e4"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=20),
        interval=_INTERVAL,
        window="20m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    # 4 cycles total: up, down, degraded, up -> 2 passing / 4 total.
    assert result.total_verdicts == 4
    assert result.passing_verdicts == 2
    assert result.availability_pct == 0.5


def test_availability_pct_excludes_maintenance_from_both_sides():
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.DOWN, "us-east", offset=timedelta(minutes=5), event_id="e2"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=10), event_id="e3"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=15), event_id="e4"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)
    maintenance_cycle_start = _SINCE + timedelta(minutes=5)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=20),
        interval=_INTERVAL,
        window="20m",
        maintenance=lambda cycle_start: cycle_start == maintenance_cycle_start,
        computed_at=_COMPUTED_AT,
    )

    # The DOWN cycle is under maintenance: excluded from both sides of the
    # ratio via `total - maintenance`. `total_verdicts` counts all 4 cycles
    # (maintenance included, per dossier §11's `passing / (total -
    # maintenance)` formula); the denominator nets out to 3, of which all 3
    # non-maintenance cycles pass. Without exclusion this would be 3/4 =
    # 0.75; with it, 3/3 = 1.0.
    assert result.total_verdicts == 4
    assert result.passing_verdicts == 3
    assert result.maintenance_verdicts == 1
    assert result.availability_pct == 1.0


def test_availability_pct_excludes_gaps_from_the_denominator():
    # Only 2 of 4 expected 5-minute cycles have any observation at all; the
    # other 2 are gaps and (default `exclude` policy) never enter total.
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.DOWN, "us-east", offset=timedelta(minutes=15), event_id="e2"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=20),
        interval=_INTERVAL,
        window="20m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.total_verdicts == 2
    assert result.passing_verdicts == 1
    assert result.gap_verdicts == 2
    assert result.availability_pct == 0.5


def test_availability_pct_uses_collapse_rule_for_mixed_locations_in_one_cycle():
    # Same cycle (same 5-minute bucket), two locations: one up, one down ->
    # collapse's rule makes this DEGRADED, which does not pass.
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.DOWN, "eu-west", offset=timedelta(minutes=1), event_id="e2"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=5),
        interval=_INTERVAL,
        window="5m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.total_verdicts == 1
    assert result.passing_verdicts == 0
    assert result.availability_pct == 0.0


def test_availability_result_carries_through_window_label_and_computed_at():
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=5),
        interval=_INTERVAL,
        window="5m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.window == "5m"
    assert result.computed_at == _COMPUTED_AT


# --- AC2: completeness% — location-aware denominator (dossier §11) ----------
#
# completeness_pct = actual / (intervals * distinct_locations), where
# intervals = window / interval (the count of expected cycles) and
# distinct_locations = COUNT(DISTINCT location) actually observed. This is
# deliberately the OTHER grain from availability_pct: it counts raw
# observations, never collapsed verdicts, and must never share a denominator
# with availability (dossier §11 "two grains... must never share a
# denominator").


def test_completeness_pct_single_location_full_coverage_is_one_hundred_percent():
    # 4 expected 5-minute cycles, 1 location, all 4 actually observed.
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=5), event_id="e2"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=10), event_id="e3"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=15), event_id="e4"),
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=20),
        interval=_INTERVAL,
        window="20m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.distinct_locations == 1
    assert result.completeness_pct == 1.0


def test_completeness_pct_three_locations_full_coverage_never_exceeds_one_hundred_percent():
    # AC2's headline case: a 3-location signal, every cycle fully reporting
    # from all 3 locations, must read exactly 100% -- never 300%. 4 expected
    # cycles x 3 locations = 12 expected observations; exactly 12 arrive.
    observations = []
    event_id = 0
    for offset_minutes in (0, 5, 10, 15):
        for location in ("us-east", "eu-west", "ap-south"):
            event_id += 1
            observations.append(
                _observation(
                    Health.UP,
                    location,
                    offset=timedelta(minutes=offset_minutes),
                    event_id=f"e{event_id}",
                )
            )
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=20),
        interval=_INTERVAL,
        window="20m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.distinct_locations == 3
    assert result.completeness_pct == 1.0


def test_completeness_pct_partial_coverage_is_actual_over_expected():
    # 4 expected cycles x 2 locations = 8 expected; only 6 observations
    # arrive -> 6/8 = 0.75.
    observations = [
        _observation(Health.UP, "us-east", offset=timedelta(minutes=0), event_id="e1"),
        _observation(Health.UP, "eu-west", offset=timedelta(minutes=0), event_id="e2"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=5), event_id="e3"),
        _observation(Health.UP, "eu-west", offset=timedelta(minutes=5), event_id="e4"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=10), event_id="e5"),
        _observation(Health.UP, "us-east", offset=timedelta(minutes=15), event_id="e6"),
        # eu-west misses cycles at minute 10 and minute 15: 2 missing of 8.
    ]
    repo = _repo_with(observations)
    calculator = _calculator(repo)

    result = calculator.compute(
        _SIGNAL,
        since=_SINCE,
        until=_SINCE + timedelta(minutes=20),
        interval=_INTERVAL,
        window="20m",
        maintenance=lambda cycle_start: False,
        computed_at=_COMPUTED_AT,
    )

    assert result.distinct_locations == 2
    assert result.completeness_pct == 0.75


# --- AC3: group rollup — min of children, counts sum (dossier §11) ---------
#
# A group's availability/completeness is the MIN of its children's
# percentages (a group is only as available as its worst component);
# counts (verdicts, passing, maintenance, gaps) SUM across children.
# Children with no data (percentages None) are excluded from the min
# but their absence stays visible — i.e. they still contribute to the
# rolled-up counts/distinct_locations rather than vanishing silently.


def _result(
    *,
    availability_pct: float | None,
    completeness_pct: float | None,
    total_verdicts: int = 0,
    passing_verdicts: int = 0,
    maintenance_verdicts: int = 0,
    gap_verdicts: int = 0,
    distinct_locations: int = 0,
    window: str = "20m",
) -> AvailabilityResult:
    return AvailabilityResult(
        availability_pct=availability_pct,
        completeness_pct=completeness_pct,
        total_verdicts=total_verdicts,
        passing_verdicts=passing_verdicts,
        maintenance_verdicts=maintenance_verdicts,
        gap_verdicts=gap_verdicts,
        distinct_locations=distinct_locations,
        window=window,
        computed_at=_COMPUTED_AT,
    )


def test_rollup_group_percentages_are_the_min_of_children():
    children = [
        _result(availability_pct=1.0, completeness_pct=0.9),
        _result(availability_pct=0.5, completeness_pct=1.0),
        _result(availability_pct=0.8, completeness_pct=0.6),
    ]

    rolled_up = rollup_group(children, window="20m", computed_at=_COMPUTED_AT)

    assert rolled_up.availability_pct == 0.5
    assert rolled_up.completeness_pct == 0.6


def test_rollup_group_counts_sum_across_children():
    children = [
        _result(
            availability_pct=1.0,
            completeness_pct=1.0,
            total_verdicts=4,
            passing_verdicts=4,
            maintenance_verdicts=0,
            gap_verdicts=1,
            distinct_locations=2,
        ),
        _result(
            availability_pct=0.5,
            completeness_pct=0.75,
            total_verdicts=4,
            passing_verdicts=2,
            maintenance_verdicts=1,
            gap_verdicts=0,
            distinct_locations=1,
        ),
    ]

    rolled_up = rollup_group(children, window="20m", computed_at=_COMPUTED_AT)

    assert rolled_up.total_verdicts == 8
    assert rolled_up.passing_verdicts == 6
    assert rolled_up.maintenance_verdicts == 1
    assert rolled_up.gap_verdicts == 1
    assert rolled_up.distinct_locations == 3


def test_rollup_group_excludes_no_data_children_from_the_min_but_sums_their_counts():
    # A child with zero observations (availability_pct=None) must not drag
    # the min to None/0 -- but its (zero) counts still sum in, so a caller
    # can see the group includes a no-data member rather than it silently
    # disappearing.
    children = [
        _result(availability_pct=1.0, completeness_pct=1.0, total_verdicts=4, passing_verdicts=4),
        _result(
            availability_pct=None,
            completeness_pct=None,
            total_verdicts=0,
            passing_verdicts=0,
            gap_verdicts=4,
        ),
    ]

    rolled_up = rollup_group(children, window="20m", computed_at=_COMPUTED_AT)

    assert rolled_up.availability_pct == 1.0
    assert rolled_up.completeness_pct == 1.0
    assert rolled_up.total_verdicts == 4
    assert rolled_up.gap_verdicts == 4


def test_rollup_group_all_children_no_data_yields_none_percentages():
    children = [
        _result(availability_pct=None, completeness_pct=None, gap_verdicts=4),
        _result(availability_pct=None, completeness_pct=None, gap_verdicts=4),
    ]

    rolled_up = rollup_group(children, window="20m", computed_at=_COMPUTED_AT)

    assert rolled_up.availability_pct is None
    assert rolled_up.completeness_pct is None
    assert rolled_up.gap_verdicts == 8


def test_rollup_group_carries_through_window_label_and_computed_at():
    children = [_result(availability_pct=1.0, completeness_pct=1.0)]

    rolled_up = rollup_group(children, window="custom-window", computed_at=_COMPUTED_AT)

    assert rolled_up.window == "custom-window"
    assert rolled_up.computed_at == _COMPUTED_AT
