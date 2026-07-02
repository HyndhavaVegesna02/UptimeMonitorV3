# Sprint 26 — Retro

**Date:** 2026-07-02
**Sprint:** STORY-041 (2 pts) + STORY-015b (3 pts) = 5 committed / 5 accepted. Shell hardening +
the first real frontend tab (Dashboard).

## What went well
- **Cleanest multi-story sprint yet.** Both stories first-pass: 041 gate-only clean; 015b both Opus
  reviewers PASS (spec, all 4 AC) / APPROVE (quality, 0 Critical, 0 Major). Zero fix loops, zero
  blocks. Only one doc-only nit (a stale docstring), folded inline.
- **Commit-after-green cadence held a second sprint running** (10 TDD commits across the two
  stories) — confirming the in-process Sonnet 5 mode reliably fixes the external single-commit
  problem the pre-revert retros flagged three times.
- **041-before-015b sequencing paid off.** The Dashboard tab was built on the hardened client +
  modular MSW handlers, so the per-tab template the five remaining tabs copy is already clean — and
  the "lift `useComponents` into a shared `useFetch<T>` when the 2nd hook lands" trigger is
  documented in `frontend-zone.md` rather than discovered as drift later.
- **Deferring 041's blast-radius to the single sprint-end compile pass** (rather than
  update-then-restale, since 015b touched the same files) was efficient and correct — one clean
  `frontend-zone.md` update covering both stories.

## What we learned (the amendment candidate)
- **Planning caught an AC the API could not satisfy.** The re-refined 015b AC asked for a
  per-component "last-observed timestamp," but the backend `ComponentDTO` is `{id, name, status}`
  only. Verifying the DTO against the AC at planning — before lock/dispatch — let me trim it to what
  the API provides and note the richer view as a future backend-DTO story. Had it not been caught,
  it would have become a mid-sprint block or a wrong implementation. The five remaining tabs
  (015c–015g) each cite specific API fields, so this check has direct recurring value.

## Amendment ADOPTED (PO-approved 2026-07-02)
1. **A consumer/tab story's AC that names specific data fields is verified against the actual backend
   DTO (`backend/src/api/v1/<feature>/models.py`) at planning, before lock.** A field the API does
   not expose is trimmed from the AC (or split into a separate backend-DTO story) — never locked
   into an AC the frontend cannot satisfy without a backend change the sprint doesn't include.
   Motivated by Sprint 26, STORY-015b (the timestamp field, caught at planning). Directly relevant
   to 015c–015g, which each render specific DTO fields. Written into `.scrum/working-agreements.md`
   (2026-07-02) with its motivating incident.

## Carry-forward (backlog / next-planning, not amendments)
- **015c planning:** (a) lift `useComponents` → a shared `useFetch<T>` when the 2nd fetch hook lands
  (parallel-shape trigger; flagged in `frontend-zone.md`); (b) a convention call on whether to
  double-test a fetch path at both hook + page level (015b does both — defensible, but decide the
  norm before it's copied).
- Orchestrator shell hygiene (self-note, not a team rule): a git-commit message with embedded quotes
  and a bash `for`-loop both mis-fired under PowerShell this sprint — use single-line commit
  messages / the Bash tool for loops to avoid re-runs.

## Process metrics
- Reviewer rejections: 0 (both first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 041 = 2, 015b = 3; no overrun. Commit cadence held.
- Velocity: 5/5. Recorded last-3 entries (22, 25, 26) = 3, 5, 5 → next-sprint mean 4.33.
