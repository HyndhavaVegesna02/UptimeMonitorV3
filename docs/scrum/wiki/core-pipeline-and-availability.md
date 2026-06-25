---
title: Zone 4 — the core pipeline (collapse + streak) and the availability engine
code_refs: [backend/src/core/services/pipeline.py, backend/src/core/services/availability.py, backend/tests/test_pipeline.py, backend/tests/test_streak.py, backend/tests/test_availability.py]
verified_sha: 98bebe9
verified_sprint: sprint-7
status: verified          # verified | stale | archived
---

## Facts (verified against code)

Zone 4's PURE core logic in `core/services/` — provider-blind, in-memory-fake-tested, imports only
`src.core.*`. Consumes canonical observations + the `Verdict` type (see
[[canonical-types-and-ports]]); reads observations through the `ObservationRepository` port. The
boundary CI floors are catalogued in [[architecture-boundary]].

### Core pipeline stages 1-2 (`core/services/pipeline.py`, STORY-010, dossier §10)
- `collapse(observations: Sequence[SignalObservation], *, under_maintenance: bool) -> Verdict`
  (`pipeline.py:36`) — stage 1. Assumes all observations belong to one signal + one cycle (the
  caller groups; collapse does not). `under_maintenance` is an INJECTED boolean, never a DB/table
  lookup, so the function stays pure. When `True`, returns a `Verdict(under_maintenance=True,
  health=None)` immediately — maintenance short-circuits before health is ever computed (AC2).
  Otherwise delegates to `_collapse_health`: all `up` -> `up`; all `down` -> `down`; any mix
  (including all-`degraded`) -> `degraded` (AC1). Raises `ValueError` ("collapse requires at least
  one observation for a cycle") on an empty sequence (sprint-6 fix loop 1).
- `Streak` (frozen, `pipeline.py:22`) `{health:Health, length:int}` — the current streak's health
  and consecutive count.
- `streak(verdicts: Sequence[Verdict]) -> Streak | None` (`pipeline.py:88`) — stage 2. `verdicts`
  is ordered oldest-to-newest; filters out every `under_maintenance` verdict first, then reads the
  remaining sequence backward from the most recent, counting while health matches and stopping at
  the first change (AC3). Maintenance verdicts are excluded entirely — they neither count nor break
  a surrounding run (AC2). Returns `None` if every verdict supplied is maintenance.
- Stages 3-4 (anti-flap + decide) are OUT OF SCOPE here — STORY-024.

### The availability engine (`core/services/availability.py`, STORY-011, dossier §11)
- `AvailabilityResult` (frozen Pydantic, `availability.py:37`) — the §11 result shape:
  `availability_pct: float|None`, `completeness_pct: float|None`, `total_verdicts: int`,
  `passing_verdicts: int`, `maintenance_verdicts: int`, `gap_verdicts: int`,
  `distinct_locations: int`, `window: str`, `computed_at: datetime`. Either percentage is `None` on
  a degenerate denominator (AC6) — never a sentinel `0.0`/`-1`, never a `ZeroDivisionError`.
- `AvailabilityCalculator` (`availability.py:110`) — the entry point, constructed with
  `observation_repo: ObservationRepository` injected (no global, no SQL). `compute(signal_key, *,
  since, until, interval, window, maintenance, computed_at)` is the only method; `interval`,
  `window`, `maintenance` (a predicate over a cycle's start instant — injected, never a DB lookup,
  mirroring `collapse`'s `under_maintenance`), and `computed_at` are ALL injected parameters — no
  per-app config read, no wall-clock read, inside this service.
- **Cycle bucketing** (a calculator design call, since §11 leaves the mechanism open):
  `_bucket_into_cycles` (`availability.py:81`) slices `[since, until)` into consecutive
  `interval`-wide buckets keyed by their start instant (`since + k*interval`); every observation
  lands in exactly one bucket by `observed_at`. A bucket with zero observations never appears in
  the map — it is a gap. Each non-empty bucket is one cycle, collapsed via `collapse`, with
  `maintenance(cycle_start)` passed straight through as `collapse`'s `under_maintenance`.
- **Availability% (AC1)**: `passing_verdicts / (total_verdicts - maintenance_verdicts)` if that
  denominator is `>0`, else `None`. `total_verdicts` counts EVERY non-gap cycle (maintenance
  included); `passing_verdicts` counts only non-maintenance `Health.UP` verdicts. Gaps never reach
  `collapse`, so the default `exclude` policy falls out naturally.
- **Completeness% (AC2)**: `len(observations) / (expected_cycles * distinct_locations)` if that
  denominator is `>0`, else `None`. `expected_cycles = max(0, -((since - until) // interval))` — the
  CEILING of `(until - since) / interval`, not the floor: a partial trailing cycle still counts as
  one full expected cycle, so every in-window observation's bucket index stays within
  `[0, expected_cycles)` and `gap_verdicts` can never go negative (sprint-7 fix loop 1, quality
  CRITICAL). When `(until - since)` is an exact multiple of `interval`, ceil equals floor —
  unchanged for divisible windows. `distinct_locations = len({o.location for o in observations})` —
  observed-distinct, not a configured set, so a 3-location signal with full coverage reads exactly
  100%, never 300% (the multi-location fix, §11/T2.5).
- **Group rollup** — `rollup_group(children: Sequence[AvailabilityResult], *, window, computed_at)
  -> AvailabilityResult` (`availability.py:216`), a free function (combines already-computed
  results, not raw observations). `availability_pct`/`completeness_pct` are each `min()` over the
  children whose value is not `None` (a no-data child can't drag a healthy group to "unknown"); if
  every child is `None`, the rollup's percentage is `None`. `total_verdicts`, `passing_verdicts`,
  `maintenance_verdicts`, `gap_verdicts` SUM across ALL children including no-data ones (AC3:
  "excluded from the min but their absence stays visible") — the four fields §11's rollup sentence
  names. **`distinct_locations` is deliberately NOT summed** (summing would double-count shared
  locations); a rolled-up result reports `distinct_locations=0`, and that 0 is never fed back into a
  division. `rollup_group([], ...)` does not raise — both percentages `None`, all counts `0`.
- **Derive-on-read (AC4)**: `compute` and `rollup_group` persist nothing; every call re-reads
  `in_window` and recomputes. No cache exists; `AvailabilityCalculator`'s only state is the injected
  repo, so a short-TTL cache could wrap `compute` later without changing the class — built pure per
  the working agreement (measure before optimizing).
- Never consults `streak` (P4) — no import of it in this module. Imports ONLY `src.core.*`
  (`domain`, `ports`, `services.pipeline`) plus `pydantic`/stdlib — no vendor, HTTP, or SQL (AC5).
- The skew flag (§11 "Skew, surfaced", Tier-2 item 7) is OUT OF SCOPE — STORY-026.

## Inference (synthesis, not verified)
- Cycle-bucketing-by-`observed_at` (rather than a stored cycle key) was chosen because it needs no
  new schema field and falls out of the `in_window` read; a future per-cycle identity would only
  matter if monitors ever reported out-of-cadence.

## History
- sprint-7: created by extracting the Zone 4 service-logic Facts (collapse/streak from STORY-010 +
  the availability engine from STORY-011) out of [[canonical-types-and-ports]], which had grown
  into a catch-all whose code_refs did not even list `pipeline.py` (its collapse/streak Facts were
  uncovered by the staleness check). This article's `code_refs` cover both service modules, so the
  Facts are now staleness-checked. Verified at 98bebe9.
