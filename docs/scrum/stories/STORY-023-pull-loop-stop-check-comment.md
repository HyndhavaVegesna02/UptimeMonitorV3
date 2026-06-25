---
id: STORY-023
title: Clarify the double stop_event check in run_periodic
type: chore
---

## Context
Follow-up from Sprint 5 review (STORY-009 quality-review minor #2, non-blocking, readability
only). `run_periodic` (`backend/src/composition/pull_loop.py:82-95`) checks
`stop_event.is_set()` twice per cycle: once in the `while` condition and once again after the
cycle body (to skip the final `await asyncio.sleep(...)` when a stop is requested DURING the
cycle, e.g. inside the `on_cycle` hook). The behaviour is correct and intentional — it just
reads as redundant at a glance.

## Description
Add a brief inline comment at the second `stop_event.is_set()` check explaining WHY it exists
(to avoid one extra interval of sleep after a stop requested mid-cycle). No behaviour change.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [x] AC1: A one/two-line comment at `pull_loop.py` explains why the post-cycle
      `stop_event.is_set()` check exists (skip the final sleep on a mid-cycle stop). No logic
      change — the existing STORY-009 pull-loop tests pass unchanged.
- [x] AC2: `lint-imports` stays green (comment-only change; no import/behaviour change).

## Resolved Questions
- None. Comment-only chore.

## History
- 2026-06-25: created from Sprint 5 review (PO asked minor #2 become a follow-up story).
- 2026-06-25: implemented (commit 9e5b329) — added the explanatory comment at
  `pull_loop.py`'s post-cycle `stop_event` re-check. Done directly by the orchestrator (a
  comment-only change with no testable behaviour; the existing pull-loop tests are the
  regression guard). DoD gate green (pytest 162, lint 3 kept, FK 10/0, alembic no-op).
