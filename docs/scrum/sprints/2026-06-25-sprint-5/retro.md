# Sprint 5 — Retrospective

**Committed/accepted:** 6/6 pts (STORY-009 = 5, STORY-020 = 1). Both accepted, merged to main
(`a6c6d0d`). Velocity history now 8 / 6 / 6 / 6 / 5 / 6.

## What went well
- **The 5-pt centerpiece cleared first try.** STORY-009 (ingest service + asyncio pull loop) passed
  spec (PASS) and quality (APPROVE) with NO fix loop — a genuinely complex story (new port + core
  service + persistence adapter + loop, the §8 crash-safety ordering) landed clean.
- **Sprint 4's two amendments both held.** The implementer correctly never touched
  `sprint-current.yaml` (orchestrator-owns-board-state); and the share-assembly rule was applied —
  the quality reviewer judged the new persistence adapter acceptable mirroring, not extractable
  duplication. The amendments are doing their job.
- **Estimates accurate.** STORY-009 = 5 (no fix loop), STORY-020 = 1 (the work itself was trivial).

## What dragged
- **A subagent hit a session limit mid-step (STORY-020).** The implementer had committed step 1 +
  the shared `MalformedDqlRowError`/`require_field`, and left a coherent uncommitted step-2 test
  that only lacked an `import re`. The verify-the-tree agreement covered recovery, but there was no
  rule on *who finishes* — the orchestrator completed the ~4-line remainder directly.
- **`architecture-boundary.md` went stale AGAIN (same as Sprint 4).** Its `code_refs: [backend/src/, …]`
  flag it stale on every backend change, forcing a no-op rehab each sprint even though its Facts
  (zone tree, 3 contracts, FK boundary) never change. Recurring busywork — and a wiki-drift signal
  the retro is meant to catch.

## Estimate vs actual
- STORY-009: estimated 5, actual ~5 (clean, no fix loop). STORY-020: estimated 1, actual 1
  (the interruption was a session-budget event, not a complexity miss).

## Wiki drift
No article stale ≥3 sprints. `architecture-boundary.md`'s repeated staleness is addressed by
amendment #1 below (narrowed `code_refs`), not by recompiling the same Facts again.

## Amendments adopted (PO-approved 2026-06-25 — both written to working-agreements.md)
1. **A wiki article's `code_refs` are the files that DEFINE its subject, not every file its subject
   touches.** Over-broad directory `code_refs` are forbidden when Facts describe a stable
   contract/structure. `architecture-boundary.md`'s `code_refs` were re-scoped to `pyproject.toml`
   + `scripts/check_fk_direction.py` + the four zone-root `__init__.py` files. (Motivated by the
   sprint-4 + sprint-5 repeated staleness.)
2. **The orchestrator may finish a trivial interrupted tail directly instead of re-dispatching** —
   when a subagent is interrupted with only a trivial remainder AND a committed failing test pins
   the contract, after the verify-the-tree step; recorded as a note, full DoD (+ reviewers if size
   requires) still applies. (Motivated by STORY-020's session-limit interruption.)

## Carried into Sprint 6
- STORY-021 (reject `native_id` in DQL builder, 1 pt) — `ready`.
- STORY-023 (clarify the double stop_event check, 1 pt) — `ready`.
- STORY-022 (fail loud on a mixed-signal batch, 1 pt) — `draft` (open question: guard scope).
- Zone 4 (STORY-010 four-stage core pipeline, STORY-011 availability) — `draft`.
