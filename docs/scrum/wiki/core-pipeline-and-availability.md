---
title: Zone 4 — the core pipeline (collapse + streak + anti-flap), the availability engine, and the skew flag
code_refs: [backend/src/core/services/pipeline.py, backend/src/core/queries/availability.py, backend/src/core/services/skew.py, backend/src/core/services/decide.py, backend/src/composition/orchestrate.py, backend/tests/test_pipeline.py, backend/tests/test_streak.py, backend/tests/test_anti_flap.py, backend/tests/test_availability.py, backend/tests/test_skew.py, backend/tests/test_decide.py, backend/tests/test_orchestrate.py, backend/tests/test_orchestration_integration.py]
verified_sha: 40e2a2c
verified_sprint: sprint-62
status: verified          # verified | stale | archived
---

## Facts (verified against code)

Zone 4's PURE core logic in `core/services/` — provider-blind, in-memory-fake-tested, imports only
`src.core.*`. Consumes canonical observations + the `Verdict` type (see
[[canonical-types-and-ports]]); reads observations through the `ObservationRepository` port. The
boundary CI floors are catalogued in [[architecture-boundary]].

### Core pipeline stages 1-2 (`core/services/pipeline.py`, STORY-010, dossier §10)
- `collapse(observations: Sequence[SignalObservation], *, under_maintenance: bool) -> Verdict`
  (`pipeline.py:40`) — stage 1. Assumes all observations belong to one signal + one cycle (the
  caller groups; collapse does not). `under_maintenance` is an INJECTED boolean, never a DB/table
  lookup, so the function stays pure. When `True`, returns a `Verdict(under_maintenance=True,
  health=None)` immediately — maintenance short-circuits before health is ever computed (AC2).
  Otherwise delegates to `_collapse_health`: all `up` -> `up`; all `down` -> `down`; any mix
  (including all-`degraded`) -> `degraded` (AC1). Raises `ValueError` ("collapse requires at least
  one observation for a cycle") on an empty sequence (sprint-6 fix loop 1).
- `Streak` (frozen, `pipeline.py:26`) `{health:Health, length:int}` — the current streak's health
  and consecutive count.
- `streak(verdicts: Sequence[Verdict]) -> Streak | None` (`pipeline.py:100`) — stage 2. `verdicts`
  is ordered oldest-to-newest; filters out every `under_maintenance` verdict first, then reads the
  remaining sequence backward from the most recent, counting while health matches and stopping at
  the first change (AC3). Maintenance verdicts are excluded entirely — they neither count nor break
  a surrounding run (AC2). Returns `None` if every verdict supplied is maintenance.
- Stage 4 (decide) is OUT OF SCOPE here — it needs the proposal lifecycle / "current status"
  reads, and stays in STORY-024.

### Core pipeline stage 3 — anti-flap (`core/services/pipeline.py`, STORY-028, dossier §10)
- `AntiFlapThresholds` (frozen, `pipeline.py:126`) `{major:int, partial:int, degraded:int,
  recovery:int}` — per-app streak-length thresholds, INJECTED by the caller. `anti_flap` never
  constructs this from config/DB; the `component -> app -> block` resolution that produces these
  values (dossier §7) is config loading and stays out of scope (deferred). The dossier §10 defaults
  are `major=5, partial=3, degraded=2, recovery=2`, but they are not hard-coded anywhere in this
  module — a caller wanting the defaults must supply them explicitly.
- `AntiFlapOutcome` (frozen, `pipeline.py:153`) `{proposed_status: ComponentStatus|None,
  internal_warning: bool}` — three distinguishable, non-overlapping shapes: (a) a proposed status
  (`proposed_status` set, `internal_warning=False`); (b) an internal warning (`proposed_status=None,
  internal_warning=True`) — logged, NEVER published, never a `ComponentStatus`; (c) nothing
  (`proposed_status=None, internal_warning=False`). The fourth, incoherent combination
  (`proposed_status` set AND `internal_warning=True`) is now ENFORCED unreachable: a
  `model_validator(mode="after")` (`_require_status_warning_coherence`, `pipeline.py:172`) rejects
  it at construction with a `ValidationError`, mirroring `Verdict`'s
  `_require_maintenance_health_coherence` (STORY-025/[[canonical-types-and-ports]]) — same pattern,
  same "reject at construction, not just by convention" rationale (sprint-8 fix loop 1, quality
  MAJOR).
- `anti_flap(streak_: Streak, thresholds: AntiFlapThresholds) -> AntiFlapOutcome` (`pipeline.py:199`)
  — stage 3, a pure lookup. Branches on `streak_.health` (AC1/AC2):
  - `Health.DOWN` (failing): the severity ladder, checked most-severe-first — `length >= major` ->
    `major_outage`; else `length >= partial` -> `partial_outage`; else `length >= degraded` ->
    `degraded`; else `length == 1` -> the internal-warning outcome; else (e.g. `length == 0`, or a
    defensive negative length) -> nothing. Checking most-severe-first means a streak that also
    clears a lower rung (e.g. a pathological config where `partial == degraded`) still resolves to
    the highest rung it clears, never a weaker one.
  - `Health.DEGRADED` (sustained degraded-performance) — STORY-149: SYMMETRIC with the `DOWN`
    ladder's damping, not unconditional — `length >= degraded` -> `degraded`; else `length == 1`
    -> the internal-warning outcome; else (e.g. `length == 0`) -> nothing. Only one
    failing-adjacent bucket exists for this health (no `major`/`partial` escalation), but reaching
    it still requires the same streak length as the `DOWN` ladder's `degraded` rung. The two length
    checks are ordered `>= degraded` BEFORE `== 1` (mirroring the `DOWN` ladder), so a config with
    `degraded == 1` proposes rather than warns — identical to what `DOWN` does at that threshold.
    Before STORY-149 this branch proposed `degraded` unconditionally for ANY length — a damping gap,
    since `_collapse_health` (`pipeline.py::_collapse_health`) returns `DEGRADED` for any
    single-cycle location disagreement, so a lone one-cycle blip across locations proposed a
    public status change with zero anti-flap protection.
  - `Health.UP` (passing): `length >= recovery` -> `operational`; else -> nothing (not yet confirmed
    recovered).
  - Degenerate/boundary inputs (AC4) all have defined, no-crash behavior: length exactly at each
    threshold and just below it (tested for major/partial/degraded/recovery), length 0 for every
    health value, and a defensive negative length for `Health.DOWN` — none of these raise or
    mis-bucket; they fall through to the documented branch. `Streak(DEGRADED, length=0)` is
    unreachable from `streak()` in practice (any non-`None` streak has `length >= 1`); the length-0
    `DEGRADED` outcome documented above keeps the ladder symmetric at that unit boundary only,
    with no field impact (STORY-149 AC5).
  - Pure: no I/O, no config/DB read, imports only `src.core.domain` types + `pydantic`/stdlib (AC3).

### The availability query engine (`core/queries/availability.py`, STORY-011, dossier §11, proposal §8)
- `AvailabilityResult` (frozen Pydantic, `availability.py:40`) — the §11 result shape:
  `availability_pct: float|None`, `completeness_pct: float|None`, `total_verdicts: int`,
  `passing_verdicts: int`, `maintenance_verdicts: int`, `gap_verdicts: int`,
  `distinct_locations: int`, `window: str`, `computed_at: datetime`. Either percentage is `None` on
  a degenerate denominator (AC6) — never a sentinel `0.0`/`-1`, never a `ZeroDivisionError`.
- `AvailabilityCalculator` (`availability.py:168`) — the entry point, constructed with
  `observation_repo: ObservationRepository` injected (no global, no SQL). `compute(signal_key, *,
  since, until, interval, window, maintenance, computed_at)` is the only method; `interval`,
  `window`, `maintenance` (a predicate over a cycle's start instant — injected, never a DB lookup,
  mirroring `collapse`'s `under_maintenance`), and `computed_at` are ALL injected parameters — no
  per-app config read, no wall-clock read, inside this service.
- **Cycle bucketing** (a calculator design call, since §11 leaves the mechanism open):
  `bucket_into_cycles` (`availability.py:133`) slices `[since, until)` into consecutive
  `interval`-wide buckets keyed by their start instant (`since + k*interval`); every observation
  lands in exactly one bucket by `observed_at`. A bucket with zero observations never appears in
  the map — it is a gap. Each non-empty bucket is one cycle, collapsed via `collapse`, with
  `maintenance(cycle_start)` passed straight through as `collapse`'s `under_maintenance`.
  This helper is promoted to a public function (`bucket_into_cycles`) to be reused by both the
  availability engine and the orchestration logic.
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
  -> AvailabilityResult` (`availability.py:285`), a free function (combines already-computed
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

### The skew flag (`core/services/skew.py`, STORY-026, dossier §11 "Skew, surfaced" / Tier-2 T2.7)
- Split out of the availability calculator at refinement: a SEPARATE per-component cross-signal
  watermark comparison, never a field on `AvailabilityResult` (AC2) — completeness can be low for
  reasons unrelated to any one feeder lagging its peers, so the two signals are independent and can
  diverge (full completeness + a skewed feeder, and vice versa — both exercised in
  `test_skew.py`).
- `SignalFeeder` (frozen, `skew.py:31`) `{signal_key:str, watermark:datetime|None,
  interval:timedelta}` — one feeding signal's current watermark and its own lag tolerance, ALL
  INJECTED by the caller (no component->signals topology load, no DB/vendor/HTTP/SQL — AC3).
  `watermark` is `None` for a signal that has never advanced (AC4).
- `SkewResult` (frozen, `skew.py:54`) `{skewed:bool, lagging_signals:tuple[str,...]}` — names which
  feeders tripped the flag (in input order), not just a bare boolean, so a dashboard/proposal
  annotation can show them (§11). The `skewed == bool(lagging_signals)` coherence invariant is now
  ENFORCED at construction: a `model_validator(mode="after")`
  (`_require_skewed_lagging_signals_coherence`, `skew.py:76`) rejects both incoherent combinations
  (`skewed=True` with empty `lagging_signals`, and `skewed=False` with non-empty `lagging_signals`)
  with a `ValidationError`, mirroring `Verdict`'s `_require_maintenance_health_coherence`
  (STORY-025) and `AntiFlapOutcome`'s `_require_status_warning_coherence` (STORY-028) — same
  pattern, same rationale (sprint-8 fix loop 1, quality MAJOR). The two coherent shapes `skew()`
  itself produces are unaffected.
- `skew(feeders: Sequence[SignalFeeder]) -> SkewResult` (`skew.py:94`) — pure, no I/O. The
  reference is the MOST-RECENT peer watermark (the MAX `watermark` across feeders that have one). A
  feeder is skewed when `reference - feeder.watermark > feeder.interval` — strict `>`, lagging by
  EXACTLY its interval is NOT skewed (AC1/AC4 boundary, tested at-boundary and one-second-over). Each
  feeder's OWN `interval` governs its own tolerance (two feeders with the same lag but different
  intervals can resolve differently — tested). The feeder supplying the reference itself is never
  flagged (zero lag).
- **No-watermark rule (AC4, documented)**: a feeder with `watermark is None` can never SUPPLY the
  reference, but when at least one peer has a watermark, it is treated as MAXIMALLY lagging (skewed)
  — "no data yet" is at least as stale as any observed lag. If every feeder is watermark-less, there
  is no reference at all and nothing is flagged.
- **Degenerate inputs (AC4)**: an empty peer set, and a single-signal component (one feeder, no
  peers to lag behind), both yield `SkewResult(skewed=False, lagging_signals=())` — no crash, no
  false flag.
- Imports ONLY stdlib (`collections.abc`, `datetime`) + `pydantic` — no `src.core.*` import at all,
  let alone vendor/HTTP/SQL (AC3, the strictest purity bar in this module so far).

### Core pipeline stage 4 — decide (`core/services/decide.py`, STORY-024, dossier §10 / §12)
- `DecideAction(str, Enum)` (`decide.py:43`) — the primary outcome returned by `decide`: `noop`, `proposed`, `superseded`, `obsoleted`, or `published_recovery`.
- `DecideService` (`decide.py:61`) — concrete service that reconciles proposed status against published status and open proposals. Constructed with injected `proposal_repo: ProposalRepository` and `publisher: StatusPublisherPort`.
- **Decision & Reconciliation Logic (AC1/AC2)**:
  - If `proposed_status` is worse than `current_status` (a degradation):
    - If no open proposal exists, calls `proposal_repo.create_open`, returns `PROPOSED`.
    - If an open proposal exists but its `to_status` differs from `proposed_status`, resolves the old one as `SUPERSEDED` and creates a new open proposal for the worst, returning `SUPERSEDED`.
    - If the open proposal is already for `proposed_status`, leaves it and returns `NOOP`.
  - Else (operational or equal):
    - If an open proposal exists, resolves it to `OBSOLETED` and returns `OBSOLETED` (§12 "Recovered -> obsoleted, nothing published").
  - If `proposed_status` improves `current_status` (recovery), publishes a `StatusChange` to `StatusPublisherPort` and returns `PUBLISHED_RECOVERY` (§10 "better -> recovery auto-publishes").
  - Repository writes are committed BEFORE the publisher is called (commit-first; publish failure doesn't lose proposal updates).

### The pipeline orchestration (`composition/orchestrate.py`, STORY-016a, dossier §8 step 5)
- `orchestrate_signal(*, signal_key, config, observation_repo, maintenance_repo, component_repo, decide_service, clock) -> DecideAction` (`orchestrate.py::orchestrate_signal`) is the composition orchestrator. It executes the full pipeline for a signal:
  1. Resolves `component_id`, `thresholds`, and the `interval` (cadence) for the signal (STORY-016a).
  2. Determines the observation window: `until = clock.now()`, `since = until - (max(thresholds) + 2) * interval`.
  3. Fetches observations in the window via `in_window`, buckets them using public `bucket_into_cycles` (`availability.py::bucket_into_cycles`), and collapses them with `collapse`, passing in `is_under_maintenance(component_id, cycle_start)`.
  4. Runs `streak()` and `anti_flap()` on the collapsed verdicts.
  5. Fetches the component's status using `ComponentRepository.get`.
  6. Reconciles the proposed status against the current status using `DecideService.decide`.
- If the component does not exist in topology (`component_repo.get` returns `None`), orchestration skips decision and returns `DecideAction.NOOP` (§8 step 5).
- Best-effort publish (T1.1, STORY-016a AC3): the `decide_service` injected here MUST be wired with a best-effort publisher (`composition/publish_helper.py::BestEffortPublisher`), since `decide`'s recovery-publish branch propagates a publish failure by contract. With the wrapper, a Statuspage outage on recovery is logged + swallowed (the DB write already committed first) rather than crashing the cycle. (See [[statuspage-publish]]. The live composition root that wires this is deferred to STORY-016; today it is proven by the AC3 test.)
- STORY-045 (write-back reachability, dossier §9/§12): `decide.py` and `orchestrate.py` are themselves UNCHANGED — `DecideService`'s injected `publisher` just gets a richer chain (`composition/publish_helper.py::StatusWritebackPublisher`, see [[statuspage-publish]]) that writes `components.status` back before delegating. Before this story, `components.status` was never written after seeding, so `current_status` was frozen at `operational` and the recovery branch (`proposed_is_better`) was unreachable in production. `test_orchestrate.py` gained `test_recovery_publish_writes_back_component_status` (a `DecideService` wired with `StatusWritebackPublisher` writes `components.status` back after a recovery publish) and `test_degrade_approve_recover_end_to_end` (the AC5 regression: `orchestrate_signal` opens a degradation, `ApprovalService.approve` (see [[api-five-file-convention]]) writes it back to DEGRADED via the SAME shared publisher chain, and a second `orchestrate_signal` cycle now reads `current_status=DEGRADED` and fires the previously-unreachable `PUBLISHED_RECOVERY` branch).


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
- sprint-8: added the anti-flap Facts subsection (STORY-028, dossier §10 stage 3 — `anti_flap`,
  `AntiFlapThresholds`, `AntiFlapOutcome`, all in `pipeline.py`). `code_refs` gained
  `backend/tests/test_anti_flap.py` so its Facts stay staleness-checked (sprint-7 agreement). Stage
  4 (decide) remains out of scope — STORY-024. Verified at 3d4a51c.
- sprint-8 fix loop 1: closed a code-quality MAJOR — `AntiFlapOutcome` could be constructed with
  `proposed_status` set AND `internal_warning=True`, a combination its own docstring promised was
  impossible. Added `_require_status_warning_coherence` (a `model_validator(mode="after")`,
  same pattern as `Verdict`'s STORY-025 validator) to reject it with a `ValidationError`; the three
  valid shapes are unaffected. Verified at 767fbae.
- sprint-8 (STORY-026): added the skew-flag Facts subsection — `SignalFeeder`, `SkewResult`, `skew`,
  all in a NEW file `core/services/skew.py` (split out of the availability calculator at refinement,
  dossier §11 "Skew, surfaced" / Tier-2 T2.7). `code_refs` gained `backend/src/core/services/skew.py`
  and `backend/tests/test_skew.py` per the sprint-7 agreement (every Fact's cited file must be
  code_ref-covered). Title updated to mention the skew flag. Verified at 5ade223.
- sprint-8 fix loop 1: closed a second code-quality MAJOR of the same shape — `SkewResult` could be
  constructed with `skewed` and `lagging_signals` disagreeing (e.g. `skewed=True` with an empty
  tuple). Added `_require_skewed_lagging_signals_coherence` (a `model_validator(mode="after")`,
  same pattern as `Verdict` STORY-025 and `AntiFlapOutcome` STORY-028) to reject both incoherent
  shapes with a `ValidationError`; the two coherent shapes are unaffected. Verified at 9ab7dd2.
- sprint-8 (compile pass): corrected stale `file:line` citations that had drifted as the module
  grew (collapse 36→40, Streak 22→26, streak 88→100, anti_flap validator 171→172, anti_flap
  181→199; AvailabilityCalculator 110→113, rollup_group 216→232; skew validator 75→76, skew
  76→94). Code unchanged — addresses only; verified_sha stays 9ab7dd2.
- sprint-10: added core pipeline stage 4 — decide (STORY-024, dossier §10 / §12). Verified at 75674b7.
- sprint-10 (STORY-029): enforced AvailabilityResult cross-field coherence validator. Verified at 32e24de.
- sprint-11 (STORY-032): refactored DecideService to extract _open_proposal helper and add assertions on open proposal IDs. Verified at a93341d.
- sprint-29 (STORY-045): no code change to `decide.py`/`orchestrate.py` (D5 — pinned in the sprint plan); added the recovery-reachability regression Facts above and two new `test_orchestrate.py` tests proving `components.status` write-back at the recovery trigger and the full degrade→approve→recover loop. verified_sha → 7cabee7.
- sprint-43 (STORY-078): Relocated availability read-model from core/services/ to core/queries/. verified_sha → 05f640e.
- sprint-43 (quality-review fix loop, M2/m3): `core/queries/availability.py`'s module docstring —
  truncated to a 3-line stub by the STORY-078 move — was restored to the original two-grain/
  denominator/D-1/P4 prose with the relocation note appended beneath it; `skew.py` and
  `test_availability.py` had the same stale `core/services/availability.py` path reference
  repointed. The restored docstring shifted the module's line numbers, so this article's
  line-anchored citations were corrected: `AvailabilityResult` 37→40, `AvailabilityCalculator`
  113→168, `bucket_into_cycles` 127→133, `rollup_group` 232→285. No behavior/Fact changed.
  verified_sha → 10a2d73.
- sprint-62 (STORY-146): RE-VERIFIED, no content change. The nested-config migration rewrote `AppConfig(...)` construction in `test_orchestrate.py` and `test_orchestration_integration.py` — authoring syntax only. This article's claims are about the CONSUMPTION shape (`orchestrate_signal` resolving `component_id`, `thresholds` and `interval` per signal), which STORY-146 AC7/AC8 pin byte-identical: `app.signals` survives as a derived attribute and `component_for_signal`/`thresholds_for` are asserted unchanged against pre-migration literals. Claims re-checked against code, not bulk-stamped. verified_sha -> d004da7.
- sprint-62 (STORY-149): **a Fact this article previously stated was the defect, written down.** The
  anti-flap subsection said `Health.DEGRADED` is "always `degraded`, regardless of length — there is
  only one failing-adjacent bucket for this health, so no length comparison applies" — faithfully
  mirroring `pipeline.py`'s own docstring, which is how a damping hole survived every verification
  pass since sprint-8: article and code agreed, so the staleness machinery had nothing to catch. The
  premise ("only one bucket") is true; the conclusion ("so no length check") never followed from it.
  `anti_flap`'s `DEGRADED` branch now requires `length >= thresholds.degraded`, warns internally at
  `length == 1`, and proposes nothing otherwise — the Facts above are rewritten to the new rule and
  to the check ORDER (`>= degraded` before `== 1`, so `degraded == 1` behaves like `DOWN` at the same
  threshold). Two existing tests asserted the old rule and were rewritten, not deleted
  (`test_degraded_streak_of_length_one_yields_internal_warning`,
  `test_degenerate_degraded_streak_of_length_zero_yields_nothing_not_a_crash`); two were added for
  the below-threshold band and the unchanged sustained case. The `DOWN` and `UP` ladders are
  byte-identical in the diff (AC8). No `decide`/`orchestrate` change was needed —
  `orchestrate.py`'s NOOP-on-`proposed_status is None` path already absorbs the two new
  nothing-proposed outcomes; verified at plan time and re-confirmed by a reality gate that drove
  `orchestrate_signal` over seeded multi-location observations and, run again at the pre-fix commit
  in a worktree, failed on exactly the five checks the fix is responsible for. Phase 2 (breadth as a
  severity ceiling, and the `degraded` semantic conflation) is NOT here — see D1/D2 in
  `docs/scrum/sprints/2026-07-28-sprint-62/decisions-and-future-work.md`. verified_sha -> 40e2a2c.
