# Sprint 47 Review — dev-db gate false-red + two highest-stakes DynamoDB adapters

**Delivery mode:** external (PO-driven agent). Verified on resume under the external-mode
floor: spec + quality review per story regardless of points, an independent full nine-command
gate re-run on the final HEAD, and the reality gate. External delivery arrived as an uncommitted
working tree (no TDD commit cadence) — the orchestrator examined every diff and committed each
story as its reviewable object before reviewing (`28eefbe`, `033bdb3`, `dc82e06`).

## Story outcomes

### STORY-080 — dev_db harness: kill the standing gate false-red (5 pts)
- **Spec:** effectively MET (the reviewer's run was inconclusive due to its own leftover manual
  containers on port 55433; the orchestrator then ran the full `test_dev_db_*` family together on
  a clean slate — **17/17 passed**, including the two historically gate-false-redding tests
  (`test_container_is_torn_down_even_when_a_test_using_the_fixture_fails` and both CLI tests). The
  standing false-red the retro escalated is resolved.)
- **Quality:** FIX_REQUIRED → **FIXED**. One MAJOR: `wait_for_postgres` caught bare
  `except (ImportError, Exception)`, silently retrying ANY connection error (wrong password/DB,
  auth failure) until timeout — manufacturing the exact opaque false-red this story exists to
  kill. Fixed in `987453b`: import guarded by `except ImportError`; connection retry scoped to
  `psycopg.OperationalError`; all other errors propagate fast + legibly. Transient-recovery test
  still green. Docstring-grammar minor folded in.
- **Reality gate:** PASS — the collision-proofing was exercised against a real blocker container
  on the old fixed port/name (autouse fixture), and the family passed together under combined load.

### STORY-084 — DynamoDB observation adapter (5 pts)
- **Spec:** PASS — all 7 AC MET with a full AC-to-test trace; reviewer ran all 5 tests green
  against real DynamoDB-Local + Postgres. AC1 cross-attribute idempotency, AC3 half-open boundary,
  AC4 real `LastEvaluatedKey` pagination (forced >1 page), AC6 availability parity (both adapters
  run + compared field-by-field) all genuinely verified. `composition/` untouched (AC7).
- **Quality:** APPROVE. Clean on all five weighing points (client-via-resource access, serde reuse,
  pagination correctness, half-open window, specific `TransactionCanceledException` handling); no
  tests-that-lie (real backend, real parity comparison). One MINOR (redundant `Decimal` isinstance
  branches) fixed in `143f15a`.
- **Reality gate:** PASS — the adapter's live vendor-path (TransactWriteItems, paginated Query,
  availability parity) is exercised against a real DynamoDB-Local container, not mocked boto3.

### STORY-085 — DynamoDB proposal adapter (5 pts)
- **Spec:** PASS — all 6 AC MET; all six port methods implemented + tested; ran green against real
  DynamoDB-Local; the real `ApprovalService` (not a stub) drives the decide→approve parity test,
  with commit-first publish verified vs the Postgres adapter. `composition/` untouched.
- **Quality:** FIX_REQUIRED → **FIXED**. One MAJOR (independently flagged by BOTH reviewers): the
  `record_approval_event` try/except was dead code (`if code==...: pass` then unconditional
  `raise` — identical to no handler, with comments implying a differentiated path that didn't
  exist). Removed in `45aa5a4`; `transact_write_items` raises naturally (recording an event on a
  missing proposal is not permitted — the intended behavior). Tests green.
- **Reality gate:** PASS — atomic uniqueness transaction, counter IDs, resolve atomicity, and the
  full real-service lifecycle exercised against a real DynamoDB-Local container.

## Fixes applied by the orchestrator (edge-case #13 trivial tails, all on external code)

| Commit | Story | Severity | Change |
| ------ | ----- | -------- | ------ |
| `987453b` | 080 | MAJOR + minor | Scope readiness retry to `psycopg.OperationalError`; guard import; docstring grammar |
| `45aa5a4` | 085 | MAJOR | Remove dead-code `record_approval_event` handler |
| `143f15a` | 084 | MINOR | Collapse redundant `Decimal` isinstance branches; drop unused import |

All three fixes verified: ruff clean; readiness 9/9; DynamoDB adapters 11/11; then the full gate
(below).

## Deferred to follow-up (NOT fixed — judgment/behavior, not trivial tails)

Captured for the PO rather than silently expanding scope:
- **STORY-085 MINOR:** the `record_approval_event` "rejected"-action event Put lacks an
  `attribute_exists(pk)` guard, so an event against a missing proposal would write an orphan —
  unreachable via `ApprovalService._decide` (which loads + resolves first), but a latent
  divergence from the Postgres FK guard. Follow-up-chore candidate.
- **STORY-080 MINOR:** the autouse blocker-container fixture ignores docker return codes, so if the
  blocker fails to start, the collision-proof claim is silently untested (the tests use dynamic
  names/ports, so they pass regardless — the blocker is decorative, not load-bearing). Consider
  asserting the blocker started, or dropping it. Cleanup itself is leak-free (post-yield finalizer).
- **STORY-085 MINOR:** `create_open` duplicates the field-copy blocks for `meta_item`/`slot_item` —
  candidate for a small shared helper.

## Independent full nine-command DoD gate (external-mode evidence of record)

**ALL NINE GREEN on HEAD `143f15a`** (full block in `sprint-current.yaml::final_gate`). Highlights:
`pytest` 611 passed (221.96s, exit 0 — no contention false-red this sprint; STORY-080's fix +
clean-container hygiene held); import-linter 8/8; ruff check + format (223 files); npm test 363,
build, lint.

One procedural note: the standalone gate run left `DATABASE_URL` / `DATABASE_URL_DIRECT` unset, so
`check_fk_direction.py` and `alembic upgrade head` initially errored on missing env — **not** a code
failure and **not** the STORY-080 contention flake (the DB-gated *tests* self-provision via the
`migrated_db` fixture and passed inside `pytest`; only the two standalone CLI commands read the env
vars directly). Both re-ran **green at the same HEAD** against a freshly provisioned throwaway DB
(`dev_db.py up`), per the documented DB-gated procedure. This was an orchestrator gate-invocation gap,
now closed.

## Wiki

STORY-080 updated `dev-setup-and-dod.md` + `migrations-and-db.md` (readiness retry + collision-proof
free-port/unique-name behavior) — content verified accurate. The orchestrator's fix commit re-staled
them by `verified_sha` arithmetic (`dev_db.py` touched again); re-verified (sha bump) since the
described behavior is unchanged by the scoped-exception refinement. Sweep otherwise clean; facts +
links clean. (Advisory `refs` amplifier notes on `run.py`/`pyproject.toml`/`check_fk_direction.py`
are pre-existing, not introduced this sprint.)

## PO verdict (2026-07-15)

**ACCEPT WITH FOLLOW-UP** — all three stories accepted (15/15 points), merged to main. The three
deferred MINORs are filed as **STORY-091** (chore, draft — needs an estimate at next refinement).

15/15 points delivered and verified; both MAJORs found by review were fixed and re-verified. This is
the second consecutive successful external delivery, and the external-mode floor again earned its
keep — it caught two MAJORs (one of which directly undermined a story's own purpose) that the
self-reported "all nine gates clean" summary did not mention.
