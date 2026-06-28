---
id: STORY-039
title: Isolate DB-gated tests so the suite is order/state-independent on a reused DB
type: chore
---

## Context
Surfaced during the Sprint 14 review. The `migrated_db` fixture (`backend/tests/conftest.py`)
supports REUSING an already-provisioned database (when `DATABASE_URL`/`DATABASE_URL_DIRECT` are set)
— but some DB-gated tests assume clean tables and collide when run against a DB that already holds
rows from a prior full run. Observed: `test_rejected_observation_save_writes_a_row_with_reason_and_payload`
and `test_rejected_observation_save_allows_null_signal_key` (and ~2 others) FAIL when the full suite
runs against a reused container, yet PASS on a fresh DB and PASS in isolation. CI is fresh-per-session
so this does not break CI today, but it makes the `pytest` DoD gate unreliable under the supported
reuse mode — and a flaky floor undermines "gates over promises."

## Description
Make DB-gated tests isolate from each other and from pre-existing data, so the full suite passes
regardless of prior DB state. Options to evaluate at refinement (pick one, apply consistently):
- a per-test transactional rollback fixture (begin/rollback around each DB test), or
- a truncate-between-tests fixture for the affected tables, or
- assertions that scope to the rows the test created (no "table has exactly N rows" assumptions).
Audit ALL DB-gated tests in `backend/tests/test_persistence_adapters.py` (and any other DB-gated
modules), not just the `rejected_observation` ones, for the same clean-table assumption.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: the full `pytest` suite passes against a REUSED, already-populated database (e.g. run the
      suite twice in a row against the same container without teardown — both runs green).
- [ ] AC2: no DB-gated test asserts global table counts / assumes an empty table; each scopes to its
      own created rows (or rolls back).
- [ ] AC3: full SIX-command DoD gate green; no production `src/` change (test-only, or a conftest
      fixture change).

## Resolved Questions
- **Approach → implementer's choice against AC1's objective bar.** Transactional-rollback,
  truncate-between-tests, or scoped-assertions — whichever is lowest-friction with the session-scoped
  `migrated_db` fixture; AC1 (suite green twice in a row against the same un-torn-down container) is
  the bar. Prefer a fixture-level fix in `backend/tests/conftest.py` over editing every test if it
  cleanly covers all DB-gated tests. (Resolved 2026-06-28.)
- **Estimate: 2** (test/fixture-only; gate-only pipeline; no production `src/` change).

## History
- 2026-06-28: created from the Sprint 14 retro (rejected_observation DB tests fail on a reused DB —
  latent test-isolation weakness; CI unaffected today).
- 2026-06-28 (Sprint 15 refinement): approach left to the implementer against AC1's objective bar.
  Status: draft → ready.
