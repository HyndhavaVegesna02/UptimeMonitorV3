# Sprint 22 — Review

**Date:** 2026-06-29
**Goal:** Close the live ingest gap surfaced by STORY-016b's AC6 run — ingest exactly one canonical
observation per execution, verified against the PO's real Dynatrace tenant.

**Committed:** 1 story / 3 pts. **Accepted:** 1 story / 3 pts (100%).

## STORY-016c — Live reconciliation: dispatch + query the canonical http_monitor_execution row — ACCEPTED (3 pts)

### What shipped
The PO's live monitor emits two event types per execution from `fetch dt.synthetic.events`:
`http_monitor_execution` (canonical per-run verdict) and `http_step_execution` (per-step companion,
sharing the same `event.id`/`timestamp`). The old dispatch registered only the step type, so the live
loop crashed with `UnsupportedMonitorTypeError`; and the shared `event.id` meant ingesting both would
collide on `UNIQUE(observations.source_event_id)`. The fix, surgical:
- `build_dql_query` now adds `event.type == "http_monitor_execution"` — excluding the step companion at
  the source so no two observations ever share an `event.id` (`query.py`, dossier §8).
- `dispatch.py::_NORMALIZERS` maps `http_monitor_execution → normalize_http_row`; the dead
  `http_step_execution` entry was removed so the registry states intent and any step row reaching dispatch
  fails loud (defense-in-depth, dossier §5).
- The recorded fixture + the three consuming test files (`test_dynatrace_adapter.py`, `test_pull_loop.py`,
  `test_grail_executor.py`) reconciled to the canonical row; a new `grail_dual_event_types.json` proves
  the dedup. The executor / normalizer body / `_assembly` / health mapping were NOT touched — they already
  handle this row.

### Acceptance criteria
- **AC1** (query filters the canonical event.type) — MET (unit test asserts the filter in both forms).
- **AC2** (dispatch routes the canonical row) — MET (real-object test: health UP, latency 755ms, location,
  source_event_id, native_id).
- **AC3** (fail-loud preserved) — MET (unmapped type → `UnsupportedMonitorTypeError`; missing field →
  `MalformedDqlRowError`).
- **AC4** (fixture reconciled; 3 test files updated) — MET; no test treats the step row as canonical.
- **AC5** (one observation per execution, dedup demonstrated not tautologically) — MET (spec-confirmed).
- **AC6** (internal live verification) — **PASSED in-session.** The loop ran against the live tenant and
  ingested **119 real observations** with no crash; health UP, two synthetic locations, ns→ms latency;
  `distinct source_event_id (119) == total (119)` → no collision, proving the dedup end to end. The real
  failure `result.status` code remains TBD (no failing run could be induced) — the health mapping stays
  fail-loud until observed.

### Evidence
- **Six DoD gates green** on the clean committed tree `ed19084`, independently re-run by the orchestrator:
  pytest **426 passed**; lint-imports **5 kept / 0 broken**; check_fk_direction **11 FKs / 0 violations**;
  alembic upgrade head exit 0 (no new migration); ruff check + format clean.
- **Opus spec reviewer: PASS** (no blocking; re-ran 44 consuming tests, confirmed AC5 is not a tautology).
- **Opus quality reviewer: APPROVE** (no blocking; confirmed surgical scope, real-object tests; blessed
  the `[tool.ruff] exclude=['.agents','.venv']` as the correct DoD-gate fix — KEEP).
- One cosmetic nit folded in (`__import__('datetime')` → module `timedelta`, commit `ed19084`).
- **Wiki compile pass** (`61f4eca`): 6 articles re-verified at `ed19084`; mechanical sweep 0 stale /
  0 broken links across all 11.

### Open follow-ups (not blocking acceptance)
1. No empty-`records` → `[]` explicit test (pre-existing gap; `normalize_rows([])` is trivially `[]`).
   Candidate one-line follow-up chore.
2. Real DOWN/DEGRADED `result.status` mapping still TBD — needs an induced failing run on the live monitor;
   `map_synthetic_status` stays fail-loud (`UnknownVendorStatusError`) until then.

## Outcome
Branch `sprint-22` (10 commits from `sprint-22-start` @ `654829c`) accepted and merged to `main`.
Velocity: 3 committed / 3 accepted. The live Dynatrace ingest thread is now verified end to end internally
against the real tenant.
