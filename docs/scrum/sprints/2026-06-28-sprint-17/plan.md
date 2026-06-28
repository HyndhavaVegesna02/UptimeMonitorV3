# Sprint 17 — Plan

**Goal:** Wire the pipeline orchestration — per cycle, after ingest, run
`collapse→streak→anti_flap→decide` per signal to produce/supersede/obsolete proposals (recovery
auto-publish via a FAKE publisher) — fully fake-tested, no live creds.

**Branch:** `sprint-17` · **Start tag:** `sprint-17-start` · **Baseline:** `07cf681` (refinement on
branch; from main `e7e337d`).

**Committed: 5 pts** — STORY-016a (single-story sprint).

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)
The PO implements externally onto `sprint-17`, OR (quota permitting) the orchestrator finishes via a
**Sonnet** implementer subagent (as in sprints 14–16). This `plan.md` is the only contract. When
ready, say **"do your review"**; the orchestrator diffs `sprint-17-start..HEAD`, runs the full
six-command gate, runs the Opus reviewers, resolves the wiki blast radius (the MECHANICAL sweep), then
review → verdict → merge → retro. **TDD + commit-after-green. Scoped staging. Do NOT write `.scrum/`
board state.**

### The six-command DoD gate — exit 0 each
`pytest` · `lint-imports` (**5 kept / 0 broken** — orchestrator is composition wiring; NO new
contract) · `python scripts/check_fk_direction.py` · `alembic upgrade head` · `ruff check .` ·
`ruff format --check .`. DB-gated: `scripts/dev_db.py up` → run → `down`. **No new migration.**

### Established facts the implementer builds on
- Pipeline stages (PURE core, `core/services/pipeline.py`): `collapse(observations, *,
  under_maintenance) -> Verdict`; `streak(verdicts: Sequence[Verdict]) -> Streak | None` (verdicts
  oldest→newest); `anti_flap(streak, thresholds: AntiFlapThresholds) -> AntiFlapOutcome`
  (`outcome.proposed_status: ComponentStatus | None`).
- `DecideService` (`core/services/decide.py`): `__init__(*, proposal_repo: ProposalRepository,
  publisher: StatusPublisherPort)`; `decide(*, component_id, proposed_status, current_status, now,
  reason=None) -> DecideAction`. It reads `get_open`, writes proposal/resolution, then publishes
  (commit-first). `create_open` returning `None` (concurrent open) → `NOOP` (the race is already
  handled — add no new guard).
- `core/services/availability.py::_bucket_into_cycles(observations, *, since, interval) ->
  dict[cycle_start, [obs]]` — promote to public `bucket_into_cycles` (rename + its one in-file caller).
- Config resolvers (STORY-040a, `composition/config.py::Config`): `component_for_signal(signal_key)
  -> str` (raises `UnknownSignalError`); `thresholds_for(component_id) -> AntiFlapThresholds` (raises
  `UnknownComponentError`). `SignalConfig` fields today: `signal_key, native_id, name, component_id`.
- Repos/ports: `ObservationRepository.in_window(signal_key, since, until)`;
  `MaintenanceRepository.is_under_maintenance(component_id, at) -> bool`; `ComponentRepository`
  (`list_components`); `ProposalRepository`; `StatusPublisherPort.publish(StatusChange)`.
- Fakes (`backend/tests/fakes.py`): `RecordingStatusPublisher` (records published `StatusChange`s),
  `FakeObservationRepository` (`save_new`), `FakeProposalRepository`, `FakeComponentRepository`,
  `FakeMaintenanceRepository`, `FakeClock`. The pull loop driver is `composition/pull_loop.py`
  (`run_cycle` / `run_periodic`).

---

## STORY-016a — Pipeline orchestration (5 pts) — gate + Opus reviewers

Composition-zone wiring of pure core services. No migration. No new lint contract. The check-then-act
inside `decide` is EXISTING behavior — add no new guarded write (the 2026-06-28 TOCTOU agreement adds
no new surface here).

### Phase A — folded-in prerequisites (TDD)
- [ ] **A1** Promote `_bucket_into_cycles` → public `bucket_into_cycles` in `availability.py` (rename +
      update its caller). Availability's existing tests must stay green (the rename is behavior-preserving).
- [ ] **A2** Add `interval_seconds: int` to `composition/config.py::SignalConfig` (a positive int;
      validate `> 0`). Add it to every signal in `config/apps/sockshop.yaml` (e.g. `interval_seconds: 60`).
      Update `test_config.py` for the new field (valid + non-positive→error). Expose it where the
      orchestration can read a signal's interval (e.g. a `Config` lookup `signal(signal_key)` or include
      it via the existing resolvers — pick the minimal addition; keep resolvers' existing signatures).
- [ ] **A3** Add `ComponentRepository.get(component_id) -> Component | None` to the port + `FakeComponentRepository`
      + `PostgresComponentRepository` (SELECT by id; `None` when absent). DB-gated test + fake/adapter
      parity (both `None` on not-found). Commit each green.

### Phase B — the orchestrator (TDD, fakes only)
New `composition/orchestrate.py` (or extend `pull_loop.py`). A function
`orchestrate_signal(*, signal_key, config, observation_repo, maintenance_repo, component_repo,
decide_service, clock) -> DecideAction` that:
1. `component_id = config.component_for_signal(signal_key)`; `thresholds = config.thresholds_for(component_id)`;
   `interval = timedelta(seconds=<signal's interval_seconds>)`.
2. `until = clock.now()`; `since = until − (max(thresholds.major, thresholds.partial,
   thresholds.degraded, thresholds.recovery) + 2) × interval` (enough cycles for any threshold).
3. `obs = observation_repo.in_window(signal_key, since, until)`;
   `buckets = bucket_into_cycles(obs, since=since, interval=interval)`; for each `cycle_start` in
   SORTED order → `collapse(buckets[cycle_start], under_maintenance=maintenance_repo.is_under_maintenance(
   component_id, cycle_start))`; collect the ordered verdict list.
4. `s = streak(verdicts)`; if `s is None` → return `DecideAction.NOOP` (nothing to decide).
   `outcome = anti_flap(s, thresholds)`; if `outcome.proposed_status is None` → `NOOP`.
5. `current = component_repo.get(component_id)`; current_status = `current.status` (if `current is None`
   → skip with a clear log / `NOOP` — an unseeded component has no status to compare).
   `return decide_service.decide(component_id=component_id, proposed_status=outcome.proposed_status,
   current_status=current_status, now=until)`.
- [ ] **B1** Failing test: observations sustaining a FAILING streak ≥ `major` → `orchestrate_signal`
      opens a degradation proposal (assert via `FakeProposalRepository`); a below-threshold streak opens
      nothing (AC1).
- [ ] **B2** Implement `orchestrate_signal`. Green. Commit. (Composition wiring only — no domain logic;
      docstrings cite §8/§10/§12.)
- [ ] **B3** Failing tests for the edges (AC2), with `RecordingStatusPublisher` + fakes: sustained
      recovery improving the published status → a recorded publish (`PUBLISHED_RECOVERY`); recovery
      while a degradation is open → OBSOLETED, nothing published; a worse degradation while a lesser is
      open → SUPERSEDED; a maintenance cycle excluded (does not by itself drive a degradation). Green.
- [ ] **B4** AC3: a raising fake publisher does not crash the cycle nor roll back the proposal (the
      proposal still exists after the raise). (DecideService already commits-first; assert it here.) Green.

### Phase C — driver wiring (TDD)
- [ ] **C1** Wire `orchestrate_signal` into the pull loop AFTER ingest (dossier §8 step 5): `run_cycle`
      (or a sibling that the periodic loop calls) invokes `orchestrate_signal(...)` for the signal once
      the batch is ingested. Keep the driver logic-free (only wiring). Failing test then green: a loop
      cycle over seeded observations both ingests AND produces a proposal, via fakes.

### Phase D — DB integration + blast radius + gate
- [ ] **D1** A throwaway-DB (`migrated_db`) integration test: seed observations + a component into the
      real DB, run `orchestrate_signal` against the real `Postgres*Repository` + `DecideService` +
      `RecordingStatusPublisher`, assert a real `status_proposals` row is opened.
- [ ] **D2** Wiki blast radius — run the MECHANICAL sweep (working-agreements.md 2026-06-28) over ALL
      articles and update/re-verify EVERY stale one. Expect: `canonical-types-and-ports`
      (`ComponentRepository.get`), `persistence-adapters` (the adapter), `config-layer`
      (`SignalConfig.interval_seconds`), `core-pipeline-and-availability` (`bucket_into_cycles` public,
      + a new "orchestration" Fact) — plus any others the sweep flags. Symbol citations; bump verified_sha.
- [ ] **D3** Full SIX-command gate green (DB up for FK/alembic/DB-gated pytest).

**AC mapping:** AC1 ← B1/B2; AC2 ← B3; AC3 ← B4; AC4 ← C1; AC5 ← A1/A2/A3; AC6 ← D.

---

## Standing conventions checklist (binds all new code)
- [ ] Orchestrator is composition wiring — NO domain logic; core stays pure; docstrings cite §8/§10/§12.
- [ ] `ComponentRepository.get` not-found → `None`, tested; fake/adapter parity (2026-06-26).
- [ ] `SignalConfig.interval_seconds` validated `> 0` (frozen-type invariant, 2026-06-26).
- [ ] Fake publisher only (live Statuspage is STORY-016); no live creds; pure-core/mockable-edges holds.
- [ ] No sentinel value mappings (2026-06-28); `src` never imports `tests`; scoped staging.
- [ ] Wiki blast-radius = the mechanical sweep over ALL articles (2026-06-28).

## Notes / risks
- Top-of-range 5. If it balloons, AC1+AC4 (degradation→proposal through the loop) is the must-have;
  AC2 edges + the DB integration test (D1) round it out — flag and Block rather than guessing.
- No tooling/MCP change. No migration.
