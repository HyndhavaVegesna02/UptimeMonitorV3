# Sprint 22 — Retro

**Date:** 2026-06-29
**Sprint:** STORY-016c (3 pts committed / 3 accepted).

## What went well
- **Cleanest execution to date.** Both Opus reviewers passed first-pass (spec PASS / quality APPROVE, no
  blocking issues); only one cosmetic nit, folded in. The accumulated working agreements visibly shaped a
  surgical implementation — the implementer changed exactly the dispatch key + query filter and reconciled
  fixtures/tests, leaving the executor/normalizer/_assembly/health-mapping untouched (zero diff).
- **AC6 live verification finally PASSED** against the real tenant: 119 observations ingested, no crash,
  `distinct source_event_id == total` proving the query-filter dedup works end to end.
- **Wiki stayed honest:** the mechanical blast-radius sweep flagged 6 articles (dynatrace-adapter + 4
  pyproject-in-code_refs + the ingest article via test_pull_loop); all re-verified at `ed19084`, 0 stale /
  0 broken links across 11.
- The `.agents/` ruff-exclude foot-gun was caught and fixed transparently in its own commit, and the
  quality reviewer independently reproduced the 84-error baseline and blessed the fix.

## What hurt (the cause behind this sprint)
- **A whole sprint of rework traced to a deferred live check.** STORY-016b (Sprint 21) was accepted and
  merged with its headline AC6 ("internal live verification") deferred as a manual step. The live path had
  never been run — so the `http_monitor_execution` dispatch gap shipped to main inside an "accepted" story
  and only surfaced when the PO ran the loop in Sprint 22. Green suite + passed reviewers gave false
  confidence about a code path that had literally never executed.
- **A single-row probe picked the wrong canonical type.** The Sprint-21 probe characterized the Grail
  schema from the `http_step_execution` rows it happened to see and built to that. The production query
  actually returns BOTH `http_monitor_execution` (the real per-run verdict) and `http_step_execution` (a
  per-step companion sharing the same `event.id`). Choosing the wrong type caused both the live crash and
  a latent `UNIQUE(source_event_id)` collision hazard.

## Amendments adopted (PO-approved 2026-06-29)
1. **Live/manual verification gates the story, or it is carved out and tracked.** A story whose acceptance
   hinges on a step that can't run at review is not `done` on that AC by promise — either it runs before
   close, or it becomes its own tracked follow-up story; never an unchecked AC inside a merged story.
2. **Live-schema reconciliation enumerates the full record/event-type distribution** the production query
   returns before choosing the canonical one — not the first-row shape.

Both written into `.scrum/working-agreements.md` (2026-06-29) with their motivating incident.

## Carry-forward (backlog candidates, not amendments)
- One-line follow-up chore: an empty-`records` → `[]` explicit test for the dispatch path (pre-existing
  coverage gap, not introduced by 016c).
- The real DOWN/DEGRADED `result.status` mapping remains TBD — it needs an induced failing run on the live
  monitor; `map_synthetic_status` stays fail-loud until then. Best captured during the next live exercise
  (e.g. STORY-017 deployment or a dedicated live-failure-capture task).

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 3 pts, single story, no overrun.
- Velocity: 3/3. Last-4 (19,20,21,22) = 5,5,5,3.
