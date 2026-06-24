# Sprint 1 — Retrospective

**Outcome:** 2/2 stories accepted, 6/6 pts, merged to main @ `ac1d468`. Zone 1 complete.

## Metrics
- Velocity: committed 6, accepted 6 (cumulative 14/14 over two sprints).
- Estimate accuracy: both 3-pt stories landed in 1 attempt — no misses.
- Reviewer loops: 0 (spec PASS + quality APPROVE on first pass for both).
- Blockers: 0 · Effort-cap trips: 0 · Hotfixes: 0.
- Wiki drift: `architecture-boundary` went stale-by-arithmetic when Zone 1 landed (its
  `code_refs` cover `backend/src/`); rehabilitated in the compile pass. 1 new article
  created (`canonical-types-and-ports`). Nothing stale ≥3 sprints.

## What went well
- Clean, boring sprint — the system worked as designed end to end.
- The boundary stopped being vacuous: `core-internal-layering` now actually bites
  (ports→domain, not services). The architecture's core bet is mechanically enforced on
  real code, not just an empty skeleton.
- Refinement-resolved decisions (Pydantic frozen models, ABCs, deferred repo methods)
  held up through implementation and both reviews without rework.

## What dragged / process signal
1. **Orchestrator state edit swept into a code commit.** The board→in-progress edit to
   `sprint-current.yaml` was uncommitted at dispatch; the implementer's `git add -A` pulled
   it into `STORY-004` commit `abeb448`. Provenance smell — a state change inside a story
   commit. Caught and reported by the implementer.
2. **LF→CRLF warnings on every commit** — no `.gitattributes` normalization (Windows).

## Amendments adopted (PO-approved)
- **Clean tree at dispatch; scoped staging** — orchestrator commits board/state edits
  before dispatching; implementers never use `git add -A`. Written to
  `working-agreements.md` (2026-06-24). Addresses signal #1.

## Backlog actions
- **STORY-018** (chore, 1 pt, draft) — add `.gitattributes` to normalize line endings.
  Addresses signal #2.

## Next
- Sprint 2 candidate: Zone 2 — STORY-006 Spine schema migration (5) + STORY-007 Repository
  adapters behind the ports (3). Both need a refinement pass first. STORY-006 is the first
  story that lands real tables, so the FK-direction check stops being vacuous there.
