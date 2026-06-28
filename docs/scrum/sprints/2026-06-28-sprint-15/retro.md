# Sprint 15 — Retrospective

**Outcome:** 5/5 points accepted (STORY-014c 3 + STORY-039 2). The Zone 6 read API is complete
(per-signal availability + check history); the DB-gated test suite is now isolated on a reused DB.
Velocity history now `…, 7, 6, 5`; last-3 mean **6.0**.

## What went well
- Both stories implemented end-to-end by a **Sonnet implementer subagent** (the PO's external quota
  was unavailable), then verified + reviewed by the orchestrator — the fallback path is now routine.
- STORY-039's reused-DB property was verified by the orchestrator directly (full suite passed twice
  against the same un-torn-down container) — a flaky floor turned reliable.
- The orchestration's hidden **§7/§17 config+topology prerequisite** was caught during refinement
  investigation (BEFORE committing it to a sprint) and re-planned — the unbuilt signal→component
  mapping + threshold loader are now tracked as STORY-040 (prerequisite) → STORY-016a (orchestration).

## What surfaced
1. **Naive-timestamp 500 (quality CRITICAL).** The new availability + history validators checked
   `since`/`until` parseability but not tz-awareness, so a bare date 500'd inside the calculator's
   tz-aware compare. The peer `maintenance` validator already rejected naive datetimes — the
   implementer did not mirror it. Fixed inline (tzinfo check + naive-input regression tests).
2. **Implementer "green" ≠ reliable, again.** The Sonnet suite only exercised tz-aware inputs, so it
   passed while missing the edge case (Sprint 14 it was ruff failures). The Opus quality reviewer
   caught it. The process held — no new rule needed there; the orchestrator gate + reviewers are the
   safety net for implementer self-reports.

No blockers, no effort-cap trips, no hotfixes.

## Process change (PO-approved)
1. **New working agreement (2026-06-28):** API endpoints reject timezone-naive datetime inputs with a
   422 at the edge (mirror the maintenance/availability/history validators) + a naive-input regression
   test. Matches the system-wide UTC-aware invariant. Joins the conventions checklist.

## Process observation (no amendment)
The orchestrator proposed the orchestration as a sprint centerpiece before confirming its
prerequisites were built; it was caught in refinement investigation and re-scoped. Lesson carried
forward: investigate a candidate story's prerequisites (in code) before proposing it for a sprint, so
a blocked story isn't put forward. Already covered by "un-ready stories can't enter a sprint"; noting
for discipline, not amending.

## Backend roadmap (drafts, pre-frontend)
- **STORY-040** — §7/§17 config + boot-seeding + signal→component topology + per-app thresholds
  (the orchestration's prerequisite; refine + likely split for Sprint 16).
- **STORY-016a** — pipeline orchestration (blocked on STORY-040).
- **STORY-037** — Publications feature module.
- Then creds/account-gated: **STORY-016** (live e2e demo), **STORY-017** (deploy).
- **STORY-015** (frontend) deferred until backend is done.
