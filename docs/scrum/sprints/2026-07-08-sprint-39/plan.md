# Sprint 39 — Small debug sprint: approve/reject CheckViolation

**Goal:** Fix the approve/reject 500 (STORY-071). Root cause already found via systematic debugging.

## Root cause (confirmed)
`POST /api/v1/decisions/{id}` → 500 `psycopg.errors.CheckViolation` on
`ck_approval_events_action`. The spine constraint is `action IN ('approved','rejected')`
(`migrations/versions/3a8254bcfe59_spine_schema.py`), but `core/services/approval.py` writes the
verb: `approve()`→`action="approve"`, `reject()`→`action="reject"`. Only the `action` literal
drifted; `to_state=ProposalState.APPROVED/REJECTED` (`.value` = `'approved'`/`'rejected'`) is right.

## Fix (single, at source)
In `backend/src/core/services/approval.py`, derive the recorded action from the resolved state so
the two can't drift: pass `action=to_state.value` in the shared resolve path (`APPROVED.value ==
'approved'`, `REJECTED.value == 'rejected'`) instead of the hard-coded `"approve"`/`"reject"`
literals. (Equivalent minimal fix: change the two literals to `"approved"`/`"rejected"` — prefer
deriving from `to_state` to prevent recurrence.)

## Regression test (TDD, closes the fake/adapter-parity gap — 2026-06-26)
Write the FAILING test FIRST: a DB-gated test (uses the `migrated_db` fixture) that drives a real
approve AND a real reject through the **real** `PostgresProposalRepository`/`ApprovalService` against
the real Postgres constraint and asserts the `approval_events` row persists with
`action='approved'`/`'rejected'` (no CheckViolation). Confirm it FAILS on the current code
(CheckViolation), then apply the fix and confirm it passes. Also assert the fake and real repo agree
on the recorded action for approve/reject (parity), where practical. An endpoint-level test
(`POST /decisions/{id}` → 200 for approve and reject on an open proposal) is a fine expression of AC1.

## Conventions checklist (held at the gate)
- Fix in `core/` stays vendor-free; no import-boundary change (lint-imports 5/0).
- DB-gated tests use the `migrated_db` fixture; run as a SINGLE pytest invocation reusing the
  already-set `DATABASE_URL` (postgresql://postgres:postgres@localhost:55432/uptime) +
  `DATABASE_URL_DIRECT` (postgresql+psycopg://…) — the live writers are stopped, so no concurrency
  (2026-07-02 agreement). Do NOT spawn a second DB.
- Backend six-gate DoD: pytest / lint-imports / check_fk_direction / alembic upgrade head /
  ruff check / ruff format --check. Frontend untouched (no frontend change needed).
- Commit after each green step (scoped staging, never `git add -A`). Do NOT edit `.scrum/`.
