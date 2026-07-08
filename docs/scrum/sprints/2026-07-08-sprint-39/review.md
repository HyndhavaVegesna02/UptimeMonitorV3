# Sprint 39 Review — debug sprint (approve/reject CheckViolation)

**Outcome:** STORY-071 accepted (2/2 pts). PO-directed small debug sprint via systematic debugging.
Merged to `main`.

## STORY-071 — approve/reject 500 fixed
- **Root cause:** `core/services/approval.py` wrote `action="approve"/"reject"`; the spine constraint
  `ck_approval_events_action` allows only `'approved'/'rejected'` → `psycopg CheckViolation` → 500 →
  the frontend's "Could not record the decision."
- **Fix (source):** derive `action=to_state.value` at the single `record_approval_event` call site
  (drops the separate `action` param) so `action` can never drift from `state` again.
- **Verification (orchestrator-run, HEAD `c35af16`):** six-gate backend DoD green — pytest **515
  passed**, lint-imports 5/0, check_fk_direction 11/0, alembic OK, ruff check + format clean.
- **Regression:** `test_persistence_adapters.py` drives a REAL approve+reject through the real
  `PostgresProposalRepository`/`ApprovalService` against the live constraint — FAILED pre-fix with the
  exact `CheckViolation` (`action='approve'`), PASSES post-fix. Plus a fake/adapter parity test.
- **Coverage:** updated the pre-existing `test_approval.py`/`test_decisions.py` assertions that pinned
  the old wrong literal (rewrite, not deletion).

## Provenance
Found live during the Sprint 38 review walkthrough once real Dynatrace data flowed (after the
monitor-id hotfix) and a real proposal appeared — a latent bug the redesign work surfaced.
