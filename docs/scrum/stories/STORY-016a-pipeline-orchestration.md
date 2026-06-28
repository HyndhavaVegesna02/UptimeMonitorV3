---
id: STORY-016a
title: Pipeline orchestration — run the core per cycle to produce proposals (fake-testable)
type: feature
---

## Context
Spec: dossier §8 (pull loop: step 5 "hand newly-inserted rows to the pipeline") + §10 (collapse →
streak → anti-flap) + §12 (decide / proposal reconciliation) + T1.1 (commit-first publish). Split
from STORY-016 (the live demo). **Today the pipeline is never run** — the stages
(`collapse`/`streak`/`anti_flap`, `DecideService.decide`) exist but nothing in `composition/` drives
them; the pull loop only ingests. This story wires the per-cycle flow, **fully fake-testable, no live
creds** (the live Dynatrace/Statuspage wiring stays in STORY-016).

**Unblocked by STORY-040a** (config resolvers): `component_for_signal(signal_key)` and
`thresholds_for(component_id)` are now available.

## Design (per cycle, per signal, AFTER ingest)
The pipeline is **per-signal**; `decide(component_id, …)` reconciles **per-component**, so multiple
signals feeding one component compose through `decide`'s supersession (no separate rollup needed for
the MVP). Verdicts are NOT persisted (the no-persisted-verdicts rule), so the orchestration DERIVES
the recent verdict history from observations:
1. `ObservationRepository.in_window(signal_key, since, until)` — `until = clock.now()`,
   `since = until − (max(thresholds)+buffer) × interval` (enough cycles for the longest threshold).
2. **Bucket into cycles + `collapse` each** (oldest→newest) → an ordered verdict sequence. `collapse`
   takes `under_maintenance = MaintenanceRepository.is_under_maintenance(component_id, cycle_start)`
   per cycle.
3. `streak(verdicts)` → `anti_flap(streak, thresholds_for(component_id))` → a proposed status (or
   nothing — then skip `decide`).
4. If proposed: read the component's **current_status** (from the spine) and call
   `DecideService.decide(component_id, proposed_status, current_status, now)` → proposal /
   supersede / obsolete / recovery-publish (via a **fake publisher** in this story).

## Folded-in prerequisites (small, in scope)
- Promote `availability.py::_bucket_into_cycles` → public `bucket_into_cycles` (rename + update its
  one caller); the orchestration reuses it (DRY — working-agreements.md 2026-06-25).
- Add `interval_seconds: int` to `SignalConfig` (STORY-040a's config model) + the sample
  `config/apps/sockshop.yaml` (the per-signal cadence belongs in config). (PO, 2026-06-28.)
- Add `ComponentRepository.get(component_id) -> Component | None` (port + fake + Postgres adapter +
  DB-gated test; fake/adapter parity, `None` when absent) to read `current_status`.

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [ ] **AC1 (degradation → proposal):** an orchestration step, given observations that sustain a
      FAILING streak ≥ the component's `major`/`partial`/`degraded` threshold (fakes + a `Config` built
      in-test), opens a degradation `StatusProposal` for the resolved component (asserted via the fake
      `ProposalRepository`). A streak below threshold opens nothing.
- [ ] **AC2 (recovery + maintenance + supersession edges):** with a fake publisher and fake repos,
      tested: a sustained recovery (≥ `recovery`) that improves the published status → a publish via
      the fake publisher (`DecideAction.PUBLISHED_RECOVERY`); a recovery while a degradation is pending
      → the open proposal is OBSOLETED, nothing published; a worse degradation while a lesser one is
      open → SUPERSEDED; a maintenance cycle is excluded from the verdict (short-circuits), so it does
      not by itself drive a degradation.
- [ ] **AC3 (commit-first / best-effort, T1.1):** `decide` writes the proposal/resolution BEFORE the
      publish; a failing publisher does not crash the cycle nor roll back the proposal (tested with a
      raising fake publisher — the proposal still exists).
- [ ] **AC4 (driver wiring):** the orchestration runs as part of the pull loop AFTER ingest (dossier
      §8 step 5) — `run_cycle` (or a sibling) invokes `orchestrate_signal(...)` for the signal; the
      orchestrator holds NO domain logic (only wiring of core services + the config resolvers + repos
      + a clock). Tested via the loop with fakes.
- [ ] **AC5 (config + port additions):** `bucket_into_cycles` is public and reused (availability tests
      still green); `SignalConfig.interval_seconds` added + in the sample config + resolvable;
      `ComponentRepository.get` added with fake/adapter parity (DB-gated).
- [ ] **AC6 (full SIX-command DoD gate green):** incl. a throwaway-DB integration test running the
      orchestration against the real repositories (seeded observations → a real proposal row). No new
      migration (proposals/observations/components/maintenance tables all exist). Forward blast radius
      (the MECHANICAL sweep — working-agreements.md 2026-06-28): canonical-types-and-ports
      (ComponentRepository.get), persistence-adapters (the adapter), config-layer (SignalConfig
      interval), core-pipeline-and-availability (bucket_into_cycles public) + any others the sweep
      flags, re-verified.

## Conventions checklist
- Docstrings cite §8/§10/§12; the orchestrator is composition-zone wiring (imports core + adapters +
  config + repos), holds no business logic; core stays pure.
- `ComponentRepository.get` empty/not-found → `None`, tested; fake/adapter parity (2026-06-26).
- The MVP uses a **fake publisher** (live Statuspage = STORY-016). No live creds; pure-core/mockable-
  edges holds. Edge DTO/value mapping has no sentinels (2026-06-28). Scoped staging; `src` ⊥ `tests`.
- This story HAS a check-then-act write (`get_open` then `resolve`/`create_open` inside `decide`) —
  but that is EXISTING `DecideService` behavior (already handles the concurrent case via
  `create_open` returning `None` → NOOP); the orchestration adds no new guarded write, so no new
  TOCTOU surface.

## Resolved Questions
- **MVP scope → produce proposals with a FAKE publisher** (live wiring in STORY-016). (PO, 2026-06-28.)
- **Cadence → `interval_seconds` in `SignalConfig`** (per-signal config). (PO, 2026-06-28.)
- **Granularity → per-signal pipeline; `decide` reconciles per-component** (N:1 via supersession).
- **Verdict history → derived from observations** (bucket+collapse; not persisted).
- **current_status → read the component's spine status** via `ComponentRepository.get`.

## History
- 2026-06-28: created from the STORY-016 split; refined at Sprint 17 planning (per-signal-then-decide
  design; fake-publisher MVP; interval in config; folded-in bucket_into_cycles/ComponentRepository.get
  prerequisites). Estimate **5** (meaty: the orchestrator + 3 small prerequisites + fake + DB tests;
  patterns established). Status: draft → ready.
