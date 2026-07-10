"""The availability engine — two-grain math + group rollup (dossier §11).

Zone 4 / pure core. The system's first CALCULATOR: compute-only, no tables,
part of the constant core. It reads observations through the
`ObservationRepository.in_window` port and computes two percentages on
demand, persisting nothing (D-1). It runs in parallel to the four-stage
pipeline (`core/services/pipeline.py`) and never consults the streak (P4).

Two metrics, two grains, never sharing a denominator:
  - Availability % is computed over COLLAPSED VERDICTS (cycles): `passing ÷
    (total − maintenance)`. `up` passes; `down`/`degraded` don't; maintenance
    is excluded BOTH sides; gaps are excluded from the denominator (the
    default `exclude` policy). Reuses `collapse` (STORY-010).
  - Completeness % is computed over RAW OBSERVATIONS: `actual ÷ (intervals ×
    distinct_locations)` where `intervals = window ÷ interval` and
    `distinct_locations = COUNT(DISTINCT location)`. The location-aware
    denominator is the multi-location fix: it stops a 3-location signal
    reporting 300% completeness.

This module imports ONLY `src.core.*` — no SQL, no vendor types, no I/O. The
skew flag (dossier §11 "Skew, surfaced") is OUT OF SCOPE here (STORY-026).

Zone 4 / pure core. Fenced read-side queries subpackage (CQRS-lite, proposal
§8). Relocated from core/services/availability.py (STORY-078).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, model_validator

from src.core.domain import Health, SignalObservation
from src.core.ports import ObservationRepository
from src.core.services.pipeline import collapse


class AvailabilityResult(BaseModel):
    """The frozen result of one availability computation (dossier §11, proposal §8).

    Two independent percentages at deliberately different grains
    (`availability_pct` over verdicts, `completeness_pct` over observations),
    plus the counts that produced them, for auditability. Either percentage
    is `None` when its denominator is degenerate (AC6) — e.g. a window with
    zero observations has no verdicts to judge, so `availability_pct` is
    `None` rather than a misleading `0.0`; a zero completeness denominator
    (no observations, hence no distinct locations) is `None` rather than a
    `ZeroDivisionError`.
    """

    model_config = ConfigDict(frozen=True)

    availability_pct: float | None
    """`passing ÷ (total − maintenance)` over collapsed verdicts; `None` if degenerate."""

    completeness_pct: float | None
    """`actual ÷ (intervals × distinct_locations)` over raw observations; `None` if degenerate."""

    total_verdicts: int
    """Count of cycles collapsed in the window (includes maintenance and gaps)."""

    passing_verdicts: int
    """Count of verdicts with `health == Health.UP` (non-maintenance)."""

    maintenance_verdicts: int
    """Count of verdicts with `under_maintenance=True` — excluded from both sides."""

    gap_verdicts: int
    """Count of expected-but-missing cycles — excluded from the denominator (`exclude` policy)."""

    distinct_locations: int
    """`COUNT(DISTINCT location)` observed in the window — makes the completeness
    denominator auditable; 0 when the window has no observations at all."""

    window: str
    """The window label this result was computed over (caller-supplied, e.g. "24h")."""

    computed_at: datetime
    """The instant this result was derived — always "now", since nothing is cached or stored."""

    @model_validator(mode="after")
    def _require_coherence(self) -> "AvailabilityResult":
        """Enforce coherence invariants for availability and completeness.

        Cites: dossier §11, proposal §8
        """
        if self.total_verdicts < 0:
            raise ValueError("total_verdicts must be non-negative")
        if self.passing_verdicts < 0:
            raise ValueError("passing_verdicts must be non-negative")
        if self.maintenance_verdicts < 0:
            raise ValueError("maintenance_verdicts must be non-negative")
        if self.gap_verdicts < 0:
            raise ValueError("gap_verdicts must be non-negative")
        if self.distinct_locations < 0:
            raise ValueError("distinct_locations must be non-negative")

        # Invariant 1: availability_pct is None iff availability denominator is 0
        availability_denom = self.total_verdicts - self.maintenance_verdicts
        if availability_denom == 0:
            if self.availability_pct is not None:
                raise ValueError(
                    "availability_pct must be None when the availability denominator is 0"
                )
        else:
            if self.availability_pct is None:
                raise ValueError(
                    "availability_pct must not be None when the availability denominator is greater than 0"
                )

        # Invariant 2: If distinct_locations > 0, completeness_pct must not be None
        if self.distinct_locations > 0 and self.completeness_pct is None:
            raise ValueError(
                "completeness_pct must not be None when the completeness denominator is greater than 0"
            )

        # Invariant 3: If not a rollup and completeness denominator is 0, completeness_pct must be None
        is_rollup = self.distinct_locations == 0 and self.total_verdicts > 0
        if not is_rollup:
            completeness_denom = (
                self.total_verdicts + self.gap_verdicts
            ) * self.distinct_locations
            if completeness_denom == 0 and self.completeness_pct is not None:
                raise ValueError(
                    "completeness_pct must be None when the completeness denominator is 0"
                )

        return self


def bucket_into_cycles(
    observations: list[SignalObservation], *, since: datetime, interval: timedelta
) -> dict[datetime, list[SignalObservation]]:
    """Slice `observations` into consecutive `interval`-wide cycles starting at `since`.

    Public API — consumed by both the availability engine (dossier §11, proposal §8) and
    the pipeline orchestrator (dossier §8 step 5: "hand rows to the pipeline").

    Cycle bucketing design (a calculator design call, dossier §11 leaves the
    mechanism open): bucket *k* covers `[since + k*interval, since +
    (k+1)*interval)`, identified by its start instant `since + k*interval`.
    Every observation falls into exactly one bucket by its `observed_at` —
    floor-divide the offset from `since` by `interval`. This needs no
    cycle-key field on `SignalObservation`; it works for any signal whose
    `observed_at` values land on (or near) the configured cadence, which is
    the only shape `in_window` ever returns. A bucket with zero observations
    never appears in the returned mapping — it is a gap, handled by the
    caller comparing the expected cycle count (the CEILING of `(until -
    since) / interval` — a partial trailing cycle still counts as one
    expected cycle, so every in-window observation's bucket index stays
    within range) against `len(buckets)`.

    Only non-empty buckets are returned (a dict keyed by cycle start), so
    `len(result)` is the number of cycles that actually have data — the
    `total_verdicts - gap_verdicts` count the caller needs.
    """
    buckets: dict[datetime, list[SignalObservation]] = defaultdict(list)
    for observation in observations:
        offset = observation.observed_at - since
        bucket_index = offset // interval
        cycle_start = since + bucket_index * interval
        buckets[cycle_start].append(observation)
    return dict(buckets)


class AvailabilityCalculator:
    """Computes availability% and completeness% on demand (dossier §11, proposal §8). Zone 4.

    Constructed with the `ObservationRepository` port injected — no global,
    no SQL — so it is fully exercisable with an in-memory fake. `compute` is
    the entry point; its only state is the injected repository, so a
    short-TTL cache could wrap `compute` later (AC4) without changing this
    class. Never consults the streak (P4); reuses `collapse` (STORY-010) to
    derive one verdict per cycle.
    """

    def __init__(self, *, observation_repo: ObservationRepository) -> None:
        self._observation_repo = observation_repo

    def compute(
        self,
        signal_key: str,
        *,
        since: datetime,
        until: datetime,
        interval: timedelta,
        window: str,
        maintenance: Callable[[datetime], bool],
        computed_at: datetime,
    ) -> AvailabilityResult:
        """Compute one `AvailabilityResult` for `signal_key` over `[since, until)`.

        `interval` and `window` are INJECTED — never read from per-app
        config here (dossier §11; the composition layer supplies them).
        `maintenance` is an injected predicate over a cycle's start instant,
        mirroring `collapse`'s injected `under_maintenance` boolean — never a
        DB/table lookup, so this stays pure and testable with hand-built
        fixtures. `computed_at` is also injected (no wall-clock read here)
        so the result is fully deterministic in tests.

        Availability% (AC1): bucket `in_window`'s observations into cycles
        (`_bucket_into_cycles`), `collapse` each non-empty cycle (passing
        `maintenance(cycle_start)` straight through to `collapse`'s
        `under_maintenance`), then `passing ÷ (total − maintenance)` over
        the resulting verdicts — `up` passes, `down`/`degraded` don't,
        maintenance is excluded from both total and passing, and a missing
        cycle (a gap — no observations fell into that bucket) is excluded
        from the denominator entirely (the default `exclude` policy: it
        never reaches `collapse`, so it cannot be maintenance or passing
        either). AC6: zero observations in the window means zero cycles,
        so `availability_pct` is `None` (no verdicts to judge) rather than
        a misleading `0.0` or a `ZeroDivisionError`.

        Completeness% (AC2): `actual ÷ (intervals × distinct_locations)`
        where `intervals = ceil(window ÷ interval)` (the same `expected_cycles`
        availability computes — a partial trailing cycle still counts as one
        full expected cycle) and `distinct_locations =
        COUNT(DISTINCT location)` over the window's raw observations — NOT
        a declared/configured location set, so the denominator self-adjusts
        as locations come and go. This is the multi-location fix: without
        it, a 3-location signal would report 300% (`actual` triples while
        the single-location denominator does not). AC6: a zero denominator
        (no observations at all, hence `distinct_locations == 0`) yields
        `None` rather than a `ZeroDivisionError`.
        """
        observations = list(self._observation_repo.in_window(signal_key, since, until))

        buckets = bucket_into_cycles(observations, since=since, interval=interval)

        # CEILING, not floor, of (until - since) / interval: a partial
        # trailing cycle (the window is not an exact multiple of the
        # interval) still counts as one full expected cycle. Floor division
        # would undercount expected_cycles while `_bucket_into_cycles` (no
        # upper clamp) still buckets every in-window observation, including
        # ones that land in that partial tail -- which can push
        # len(buckets) past a floor-based expected_cycles and drive
        # gap_verdicts negative. Computed via integer floor-division of the
        # negated span (then negated back) to avoid float-rounding bugs:
        # -((since - until) // interval) == ceil((until - since) / interval).
        # When (until - since) is an exact multiple of interval, ceil ==
        # floor, so this is unchanged for every previously-passing case.
        expected_cycles = max(0, -((since - until) // interval))
        gap_verdicts = expected_cycles - len(buckets)

        total_verdicts = 0
        passing_verdicts = 0
        maintenance_verdicts = 0
        for cycle_start, cycle_observations in buckets.items():
            verdict = collapse(
                cycle_observations, under_maintenance=maintenance(cycle_start)
            )
            total_verdicts += 1
            if verdict.under_maintenance:
                maintenance_verdicts += 1
            elif verdict.health is Health.UP:
                passing_verdicts += 1

        denominator = total_verdicts - maintenance_verdicts
        availability_pct = passing_verdicts / denominator if denominator > 0 else None

        distinct_locations = len({observation.location for observation in observations})

        completeness_denominator = expected_cycles * distinct_locations
        completeness_pct = (
            len(observations) / completeness_denominator
            if completeness_denominator > 0
            else None
        )

        return AvailabilityResult(
            availability_pct=availability_pct,
            completeness_pct=completeness_pct,
            total_verdicts=total_verdicts,
            passing_verdicts=passing_verdicts,
            maintenance_verdicts=maintenance_verdicts,
            gap_verdicts=gap_verdicts,
            distinct_locations=distinct_locations,
            window=window,
            computed_at=computed_at,
        )


def rollup_group(
    children: Sequence[AvailabilityResult], *, window: str, computed_at: datetime
) -> AvailabilityResult:
    """Roll up a group's `AvailabilityResult` from its children's (dossier §11, proposal §8, AC3).

    A group is only as available as its worst component: `availability_pct`
    and `completeness_pct` are each the MIN of the children that have a
    value (i.e. excluding `None` — a no-data child cannot drag a healthy
    group down to "unknown", since `min` would otherwise need to treat
    `None` as either smallest or largest with no natural choice). If every
    child is `None`, the rolled-up percentage is also `None` (AC6's
    degenerate case propagates up rather than defaulting to some other
    sentinel).

    Counts SUM across ALL children, including no-data ones — so a no-data
    child is "excluded from the min but its absence stays visible" (AC3): it
    contributes nothing to the numerator/denominator counts that would
    inflate the group's apparent health, yet the group's `gap_verdicts`
    still reflects its presence rather than the child vanishing from the
    rollup entirely. Dossier §11 names exactly four count fields as summed:
    `total_verdicts` ("verdicts"), `passing_verdicts`, `maintenance_verdicts`,
    `gap_verdicts`. `distinct_locations` is deliberately NOT summed — it
    exists per-leaf to make ONE signal's completeness denominator auditable
    (its own docstring), and summing it across children would double-count
    shared locations and misrepresent the group as having more distinct
    probe locations than it does. A synthesized group result has no
    observation stream of its own, so `distinct_locations` is `0` here.

    `window` and `computed_at` are injected like `AvailabilityCalculator.
    compute`'s — the rollup itself derives nothing from a clock or config.
    """
    availability_values = [
        child.availability_pct
        for child in children
        if child.availability_pct is not None
    ]
    completeness_values = [
        child.completeness_pct
        for child in children
        if child.completeness_pct is not None
    ]

    return AvailabilityResult(
        availability_pct=min(availability_values) if availability_values else None,
        completeness_pct=min(completeness_values) if completeness_values else None,
        total_verdicts=sum(child.total_verdicts for child in children),
        passing_verdicts=sum(child.passing_verdicts for child in children),
        maintenance_verdicts=sum(child.maintenance_verdicts for child in children),
        gap_verdicts=sum(child.gap_verdicts for child in children),
        distinct_locations=0,
        window=window,
        computed_at=computed_at,
    )
