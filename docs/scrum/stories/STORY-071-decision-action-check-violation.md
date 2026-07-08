---
id: STORY-071
title: Defect — approve/reject 500s (approval_events.action violates ck_approval_events_action)
type: defect
---

## Context
Found live during the Sprint 38 review walkthrough (2026-07-08). Once real Dynatrace data flowed
(after the monitor-id hotfix), a real degradation produced an OPEN proposal; approving/rejecting it
on the Approvals tab failed with "Could not record the decision" (the frontend's generic failure
branch).

## Root cause (systematic-debugging, confirmed)
`POST /api/v1/decisions/{id}` returns **500** on a `psycopg.errors.CheckViolation`:
`new row for relation "approval_events" violates check constraint "ck_approval_events_action"`.
The spine schema constraint is `action IN ('approved', 'rejected')`
(`migrations/versions/3a8254bcfe59_spine_schema.py`), but `core/services/approval.py` writes the
present-tense verb: `approve()` → `action="approve"` (line 63), `reject()` → `action="reject"`
(line 87). The sibling `to_state=ProposalState.APPROVED` (`.value == 'approved'`) is correct — only
the `action` literal drifted from the schema.

**Why it was never caught:** a fake/adapter-parity gap (2026-06-26 agreement). The in-memory fake
`record_approval_event` stores `'approve'` with no constraint; only real Postgres rejects it, and no
DB-gated test drove a real approve/reject through the constraint. The live approve path was never
exercised against real Postgres until real proposals appeared.

## Acceptance Criteria
- [ ] AC1: A real approve AND a real reject on an OPEN proposal persist an `approval_events` row
      through the real Postgres `ck_approval_events_action` constraint with NO CheckViolation, and
      `POST /api/v1/decisions/{id}` returns 200 for both. Driven by a DB-gated test against the real
      repository/approve+reject path (not the fake) — closing the parity gap.
- [ ] AC2: The stored `action` is `'approved'`/`'rejected'`, derived from the resolved
      `to_state.value` so `action` and `state` cannot drift apart again (single source).
- [ ] AC3: The fake and the real repository agree on the recorded `action` for approve/reject
      (fake/adapter parity), covered by the same contract assertion where practical.
- [ ] AC4: Backend six-gate DoD green (pytest, lint-imports, check_fk_direction, alembic upgrade
      head, ruff check, ruff format).

## Open Questions
None — root cause is pinned.

## History
- 2026-07-08: found live in the sprint-38 walkthrough; root-caused via systematic debugging.
  Status: ready. Scheduled to sprint-39 (small debug sprint, PO-directed).
