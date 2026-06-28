---
id: STORY-016a
title: Pipeline orchestration — run the core per cycle to produce proposals (fake-testable)
type: feature
---

## Context
Spec: dossier §8 (pull loop) + §10 (pipeline stages) + §12 (proposal lifecycle) + T1.1 (commit-first
publish). Split from STORY-016 at Sprint 15 planning: the *orchestration logic* is pure backend and
fully testable with fakes + a throwaway DB (no live Dynatrace/Statuspage), whereas STORY-016 is the
live-credential demo on top.

**Today the pipeline is never run.** The stages (`collapse`/`streak`/`anti_flap`,
`DecideService.decide`) and `publish_best_effort` all exist, but nothing in `composition/` calls them
— the pull loop only ingests observations into the DB. This story wires the per-cycle flow.

**Depends on STORY-040a** (config layer): the orchestration needs to resolve `signal_key→component_id`
and `component→AntiFlapThresholds`, which STORY-040a provides as in-memory config resolvers. This story
cannot start until STORY-040a lands. (It does NOT need the DB seed, STORY-040 — it reads the resolvers
from config directly.)

## Description (to refine before its sprint)
A composition orchestration that, per cycle / per component, drives:
`observations (ObservationRepository, bucketed into cycles) → collapse (with under_maintenance from
MaintenanceRepository.is_under_maintenance) → verdict history → streak → anti_flap (per-app
thresholds from STORY-040) → DecideService.decide (current_status from the component, via the
topology resolver) → proposal / recovery-publish`. All ports faked in tests; a throwaway-DB
integration test exercises the real adapters. No live creds.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: a composition orchestrator runs the full stage chain per cycle and produces an open
      proposal on a sustained degradation (asserted via the proposal repo), with fakes.
- [ ] AC2: maintenance short-circuits (a maintenance cycle yields no degradation proposal); recovery
      auto-publishes per §10 (DecideAction.PUBLISHED_RECOVERY), with a fake publisher.
- [ ] AC3: commit-first / best-effort publish (T1.1) — a failing publisher does not crash the cycle
      nor roll back the proposal.
- [ ] AC4: a throwaway-DB integration test runs the chain against the real repositories.
- [ ] AC5: full SIX-command DoD gate green; blast radius resolved.

## Open Questions
- Cadence/driver: extend the existing `pull_loop` (ingest → then orchestrate) or a separate periodic
  task? Confirm at refinement.
- How verdict history is assembled for `streak` (derive from observations like `availability.py`).
- Estimate (likely 5; refine after STORY-040).

## History
- 2026-06-28: created from the STORY-016 split (Sprint 15 planning). Status: draft — blocked on
  STORY-040; refine for a later sprint.
