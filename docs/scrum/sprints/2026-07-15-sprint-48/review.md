# Sprint 48 — Review

**Goal:** Complete the DynamoDB adapter set (publications, maintenance, rejected + dynamo
seed) proven for parity against DynamoDB-Local, and land the three sprint-47 review minors.
Neither wired into composition (cutover is STORY-087).

**Mode:** external (3rd consecutive). Delivery arrived as one uncommitted tree; orchestrator
committed per story as the reviewable object, ran the full external-mode verification floor.

**Branch:** `sprint-48` (from main `a8606e9`, tag `sprint-48-start`). Final HEAD `a03ca2e`
(code final HEAD `b9d4a5c`).

**Outcome:** both stories Done. 7/7 points delivered.

---

## STORY-086 — DynamoDB publication / maintenance / rejected adapters + dynamo seed (5 pts)

**Commit:** `d60eda0`. **Spec: PASS · Quality: APPROVE.**

Built three new adapters + a DynamoDB topology seed, all following the sprint-46/47
conventions (counter `_next_id` with distinct sks, `dynamo_serde` datetimes, `TOPOLOGY`
partition, `gsi1` index, omit-None). Not wired into composition (AC6).

| AC | Verdict | Evidence |
|----|---------|----------|
| AC1 publications | MET | counter sk="publication"; `list_recent` Query `ScanIndexForward=False`+`Limit` (no Python sort); author via BatchGetItem of `approved_actor`; empty-partition guard. `test_dynamo_publication_repository.py` (3 tests, ran live) |
| AC2 maintenance | MET | distinct counter; `list_windows` gsi1 ascending; `is_under_maintenance` inclusive-start/exclusive-end **tested at both instants** (t0→True, t1→False); `delete` raises parity error. `test_dynamo_maintenance_repository.py` (3 tests, ran live) |
| AC3 rejected | MET | `REJECTED#<key|UNKNOWN>`; None signal_key never fails; float→Decimal round-trip. `test_dynamo_rejected_observation_repository.py` (3 tests, ran live) |
| AC4 seed | MET | idempotent; config-change reflected; **status NOT reset on re-seed** (the trap — test mutates to DEGRADED, re-seeds, asserts survival). `test_dynamo_seed.py` |
| AC5 consistency delta | MET | GSI eventual-consistency documented in the maintenance adapter docstring + `wiki/persistence-adapters.md` |
| AC6 boundaries | MET | import-linter 8/8 kept; app.py/run.py/settings.py untouched |

**Quality:** APPROVE, 0 critical / 0 major. Both spec + quality reviewers verified the
gsi1sk high-sentinel range algebra (inclusive-start correct, no off-by-one) and the
BatchGetItem 100-key/UnprocessedKeys handling. 3 non-blocking minors → follow-up:
- `seed_dynamo.py:21` docstring says signals "full overwrite"; behavior is upsert-only —
  reword to "upsert".
- `dynamo_maintenance_repository.py:94` FilterExpression uses bare attribute names (correct,
  not reserved words) where the codebase elsewhere prefers `ExpressionAttributeNames`.
- (Not a code issue) one quality reviewer's env couldn't start Docker; it verified the
  sort-key algebra by hand — the spec reviewer + the orchestrator's reality gate ran the
  tests live, so this is covered.

## STORY-091 — sprint-47 review minors (2 pts)

**Commits:** `2816e5b` + review tail `b9d4a5c`. **Spec: FAIL→FIXED · Quality: APPROVE.**

| AC | Verdict | Evidence |
|----|---------|----------|
| AC1 orphan guard | MET | ConditionCheck-on-META on the non-"approved" branch (the gap); "approved" was already guarded. `test_dynamo_proposal_repository_orphan_event_guard` proves `TransactionCanceledException` + no event written for a missing proposal. **Diverged from the plan's literal `attribute_exists(pk)`-on-Put — confirmed a correction** (the literal form would have failed the happy path, since the event's own key doesn't exist yet on create). |
| AC2 blocker return-code | MET (after fix) | Option A `assert res.returncode == 0` delivered. **Spec review found + reproduced a leak:** the assert sat before `yield` with no `try/finally`, so a real blocker-start failure would raise before cleanup and leak the container — violating AC2's explicit "teardown stays leak-free" clause on the failure path. **Orchestrator tail `b9d4a5c`** wrapped assert→yield in `try/`, moved `docker rm -f` into `finally` (idempotent). |
| AC3 create_open dedup | MET | `_base_proposal_attrs` helper; byte-identical items; all 5 pre-existing regression tests pass unmodified |
| AC4 gates | MET | see full-gate below |

**Quality:** APPROVE, 0/0/0 — and independently confirmed the AC1 divergence was the *correct*
mechanism, not a shortcut.

---

## Verification floor (external mode)

**Independent full nine-command DoD gate — orchestrator's own run on final HEAD `b9d4a5c`
(NOT the external agent's self-report). ALL NINE GREEN:**

| Command | Result |
|---------|--------|
| pytest | 622 passed in 153.55s |
| import-linter | 8 contracts kept, 0 broken |
| check_fk_direction.py | 11 FKs, 0 violations |
| alembic upgrade head | OK |
| ruff check | All checks passed |
| ruff format --check | 231 files formatted |
| npm test | 51 files / 363 tests passed |
| npm run build | built (278.14 kB / gzip 85.39 kB) |
| npm run lint | clean |

DB-gated commands ran against a freshly provisioned throwaway Postgres (`dev_db.py up`), torn
down at close.

**Reality gate — live vendor path at final HEAD:** 8 tests re-run against real DynamoDB-Local
(Docker), 30.48s — publication record+list_recent, author-derivation parity (via real
`record_approval_event(action="approved")`), `is_under_maintenance` at both boundary instants,
seed status-preservation trap, orphan-event guard. The adapter paths executed for real, not
just internal consistency.

Note: the delivery self-reported "622 passed / all green" — the orchestrator's independent run
confirmed it (622, matching), per the never-trust-self-reported-gate contract.

---

## Demo
The three new adapters + dynamo seed are DynamoDB-Local-proven but **not yet wired into
composition** (by design — STORY-087 cutover). Live demo of the running app is deferred to the
cutover; this sprint's evidence is the reviewer + reality-gate test runs above.

## Follow-ups (proposed → next planning / STORY-091-style chore)
- STORY-086 quality minors: `seed_dynamo.py` docstring "overwrite"→"upsert";
  maintenance `ExpressionAttributeNames` aliasing consistency.
- Pre-existing wiki staleness: `dev-setup-and-dod.md` stale since sprint-47's DoD amendment
  (not this sprint's diff) — rehabilitate next time its refs are in a sprint.

## PO verdict
_(per story: accept → merge to main; reject → back to backlog)_
- STORY-086: ______
- STORY-091: ______
