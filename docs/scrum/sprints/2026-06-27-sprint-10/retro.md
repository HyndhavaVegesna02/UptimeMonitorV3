# Sprint 10 — Retrospective (2026-06-27)

**Outcome:** committed 6, accepted 6 (4/4 stories). Sixth consecutive 6-point sprint. Zone 4 (the
four-stage core pipeline) is complete.

## What went well
- **Velocity calibration is solid** — 6/6 for the sixth sprint running.
- **Refinement removed the risk before the sprint.** Resolving the "current published status" read
  seam at planning (inject `current_status`; defer the `components.status` read to STORY-016) meant
  `decide` was built literally to the plan and passed **spec review on the first try** — no AC
  ambiguity despite a genuinely subtle §10+§12 two-comparison rule. Reading the dossier (not guessing)
  during refinement paid off directly.
- **Proactive audit worked.** STORY-029 found a real latent gap (`AvailabilityResult` coherence
  unenforced) and closed it, instead of it surfacing as a future MAJOR.

## What dragged
- **The only blocking finding was a PLAN gap, not an impl gap.** STORY-024's `decide.py` shipped with
  no docstrings (quality MAJOR). The plan detailed the algorithm exhaustively but never required the
  docstring convention every peer core service follows. Under external implementation, plan.md is the
  *only* contract — the implementer builds literally to it and does not infer unstated conventions.
  Fixed inline (docstrings only, `ed87055`), but it cost a fix loop that the plan could have avoided.
- **Recurring cosmetic minors.** Trailing blank lines, unsorted/mixed imports — the same class shows
  up most sprints and accumulates into chores (STORY-031, STORY-032). Below the blocking bar, but a
  steady tax on the reviewer.

## Amendments (PO-approved)
1. **Plan.md carries a self-contained conventions checklist** (under external impl), with new
   modules/public APIs naming the docstring deliverable explicitly. Generalizes the sprint-9
   "plan must be self-contained" agreement into a concrete checklist (docstrings citing the dossier §,
   coherence validators, empty/boundary tests, scoped staging, follow-existing-patterns). Directly
   prevents the STORY-024 MAJOR from recurring. → working-agreements.md 2026-06-27.
2. **Add `ruff` (format + import-sort) as a mechanical DoD gate** (retro tooling decision) so the
   recurring cosmetic-minor class is caught mechanically and never reaches a reviewer. Implemented by
   **STORY-033** (add + config + one-pass format + wire into DoD/CLAUDE.md); DoD stays four commands
   until it lands. → working-agreements.md 2026-06-27.

## Follow-ups filed
- **STORY-032** (1 pt, ready) — decide.py quality minors (DRY helper, `opened.id` guard, import style,
  trailing blanks). Note: its import/trailing-blank parts will be subsumed by ruff (STORY-033); the
  DRY helper + `opened.id` guard remain its unique value — sequence STORY-033 first at planning.
- **STORY-033** (2 pts, draft) — the ruff DoD gate (one open Q: ruleset breadth, default minimal).

## Process metrics
- Stories: 4 committed / 4 done / 4 accepted. Blocked: 0. Hotfixes: 0.
- Fix loops: 1 (STORY-024 quality MAJOR, docstrings, orchestrator inline at PO request).
- Estimate accuracy: 4/4 on estimate. Wiki: 3 articles updated + re-stamped to `a93f91a`; 0 stale ≥3
  sprints.
