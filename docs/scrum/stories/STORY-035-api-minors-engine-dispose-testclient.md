---
id: STORY-035
title: API minors — dispose the app engine on shutdown + migrate off the deprecated TestClient path
type: chore
---

## Context
Two non-blocking minors surfaced by the Opus quality reviewer at the Sprint 12 review of
STORY-014 (Zone 6 / FastAPI). Neither blocked the story; bundled here as a follow-up chore.

## Description
1. **Dispose the SQLAlchemy engine on app shutdown.** `composition/app.py::create_app` builds an
   `Engine` and stores it on `app.state` but never disposes it. For a process-lifetime engine this
   is low-risk, but a FastAPI shutdown hook (`lifespan` / shutdown event) should call
   `engine.dispose()` so the app releases its pooled connections cleanly (matters for tests that
   spin many app instances and for graceful redeploys).
2. **Migrate off the deprecated Starlette `TestClient` / `httpx` path.** The test run emits
   `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2
   instead`. Resolve the deprecation (evaluate the recommended `httpx`-version / `httpx2` path or
   the current Starlette guidance) so the warning clears and the test client stays supported.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: `create_app` registers a shutdown/lifespan hook that disposes the engine; a test asserts
      dispose is invoked on app shutdown (or that no connections leak across app instances).
- [ ] AC2: the `StarletteDeprecationWarning` no longer appears in the `pytest` run (e.g. `pytest -W error`
      on that warning passes, or the warning count for it is 0).
- [ ] AC3: full six-command DoD gate green; no behavior change to the decision/health endpoints.

## Resolved Questions
- **httpx mechanism → implementer's choice, sanctioned at planning.** The fix for minor 2 may pin
  or upgrade `httpx`, adopt the recommended successor, or (last resort, with a written justification
  in the story) scope a targeted warning filter — whatever clears the warning while keeping the
  Starlette `TestClient` working. A dependency pin/upgrade here is a sanctioned tooling change made at
  Sprint 13 planning (one of the two allowed moments). AC2 is the objective bar: the warning no
  longer appears in the `pytest` run and the endpoint tests still pass. (PO-approved 2026-06-28.)
- **Estimate: 2** (two small, independent backend cleanups; gate-only).

## History
- 2026-06-28: created from the Sprint 12 retro (STORY-014 non-blocking quality minors).
- 2026-06-28 (Sprint 13 refinement): httpx mechanism left to the implementer against AC2's objective
  bar; dependency change sanctioned at planning. Status: draft → ready.
