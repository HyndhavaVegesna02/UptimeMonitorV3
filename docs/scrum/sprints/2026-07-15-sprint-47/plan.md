# Sprint 47 Plan — Kill the standing gate false-red, then the two highest-stakes DynamoDB adapters

**Status:** DRAFT — awaiting PO approval at planning.

**Sprint goal:** End the recurring `test_dev_db_*` full-gate false-red for good (STORY-080),
then advance the AWS migration epic through its two hardest adapters — the idempotent
observation ingest + half-open window read (STORY-084) and the human-approval concurrency
gate: open-slot uniqueness, counter IDs, approval events (STORY-085) — both proven for exact
behavioral parity against the landed DynamoDB-Local harness, neither wired into composition yet.

**Mode:** in-process (default — yt-implementer per story; all three are 5 pts, so spec + quality
reviewers run concurrently after each implementation, then the DoD gate, then the reality gate).

## Stories (15 pts committed)

| # | Story | Pts | Why here |
| - | ----- | --- | -------- |
| 1 | STORY-080 — dev_db harness: kill the standing gate false-red | 5 | Retro-escalated top priority. Widened at this planning (PO 2026-07-15) from the CLI-only port fix to the whole `test_dev_db_*` contention family. |
| 2 | STORY-084 — DynamoDB observation adapter (idempotent ingest + half-open window) | 5 | The epic's highest-stakes adapter: carries ingest idempotency + the single read feeding `core/queries/availability.py`. |
| 3 | STORY-085 — DynamoDB proposal adapter (open-slot uniqueness, counter IDs, approval events) | 5 | The human-approval gate's concurrency invariant; denormalizes `approved_actor` that STORY-086 later consumes. |

**Velocity honesty (size risk — flagged for PO):** recent sprints ran 5–8 pts (46:8, 45:6,
44:5, 43:8). 15 pts is roughly double that band for backend adapter work, and each of these is a
genuine 5 (real-container tests, ported concurrency/idempotency invariants, parity assertions).
Sprint 38 hit 31, but that was frontend parallel-waves, not sequential adapter TDD. This is a
stretch commit the PO chose deliberately. **Drop order if the session runs long:** STORY-085
drops first (it is last and lowest-priority; 080 and 084 are the retro's named pair), then
STORY-084. STORY-080 never drops — clearing the standing false-red is the sprint's floor.

## Execution order + reasoning

**STORY-080 → STORY-084 → STORY-085**, sequential.

- **STORY-080 first.** The retro escalated it as the sprint's floor: until it lands, every gate
  close risks a contention false-red that costs a contention-proof cycle. Landing it first means
  STORY-084's and STORY-085's own gate runs benefit from the hardened harness. It is also the
  sprint's risk concentration on the same Docker-lifecycle machinery — do it while the session is
  fresh.
- **STORY-084 before STORY-085.** Epic sequence (082→083→**084**→**085**→086…). 084 is the
  higher-stakes, more foundational adapter (ingest idempotency feeds the whole pipeline; the read
  feeds availability). 085's approval-event denormalization (`approved_actor`) is consumed only by
  the later STORY-086, so nothing in 085 blocks on 084 — the ordering is risk/importance, not a
  hard dependency.

## Tooling gaps

None. Docker 28.5.2 present; `boto3` already a dependency (added STORY-082); the DynamoDB-Local
harness (`scripts/dynamo_local.py`, `dynamo_local` / `dynamo_resource` / `clean_dynamo_tables`
fixtures, `dynamo_serde.py`) all landed in sprint 46. `cfn-lint` NOT needed (joins the DoD at
STORY-088). No new MCP/CLI.

## Plan-verifier dispatch (v2.1.2 conditional rule)

**Dispatched** — this sprint IS contract-sensitive on two of three stories:
STORY-084 and STORY-085 are adapter/vendor-path stories that port units/scale-sensitive and
concurrency-sensitive invariants (idempotency uniqueness key; half-open `[since, until)` boundary;
one-open-proposal-per-component transaction; strictly-increasing counter IDs) and each carries a
behavioral-parity AC against the Postgres adapter. STORY-080 is internal test-harness work (not
contract-sensitive on its own) but rides along. The verifier checks the ported semantics against
the producing Postgres code and the landed DynamoDB-Local harness before the PO locks.

**Verifier result (2026-07-15): contract-faithful** — 12 of 13 checks PASS; one GAP fixed
pre-lock (STORY-085 `StatusProposal.id` is `int | None`, not `int` — corrected in the story
file + the verified-contracts section above). Two non-gap notes folded into the story plans
below for the implementer briefs:
- **Transactions need the client, not just the resource.** The landed read adapters use only
  `db_resource.Table(...)`. STORY-084's `TransactWriteItems` and STORY-085's `UpdateItem ADD`
  counter need the client-level API (`db_resource.meta.client.transact_write_items(...)` / a
  Table `update_item` with an `ADD` update-expression) — reached through the same resource the
  `dynamo_resource` fixture yields.
- **Pagination is genuinely new.** The landed read adapters (`dynamo_signal_repository`,
  `dynamo_component_repository`) do a single `query()` and read `Items` once — they do NOT loop
  on `LastEvaluatedKey`. STORY-084 AC4 requires paginated `in_window`; reviewers must NOT accept
  a copy of the existing single-page idiom as satisfying AC4.

## Definition of Done — state this sprint

The AWS-epic DoD amendment (retire `alembic upgrade head` + `check_fk_direction.py`; adopt the
DynamoDB-Local pytest floor; add `cfn-lint`) is **PENDING — NOT in force**; it takes effect only
at STORY-087/088. This sprint touches neither Postgres schema/migrations nor CloudFormation, so:

- The full **nine-command** gate stays in force unchanged (6 backend incl. alembic + FK-check,
  3 frontend). This sprint's diffs are backend-only (Python tests/adapters) — the frontend three
  are unaffected but still run at the full close gate.
- **Scoped mid-sprint gates (2026-07-14(a)):** per-story `yt_gate.py --only` limited to the
  commands each story's diff can affect. STORY-080 touches `backend/tests/` + `scripts/` (no
  schema) ⇒ `--only pytest,importlinter,ruff-check,ruff-format`; STORY-084/085 add adapter code
  under `adapters/persistence/` (no migration) ⇒ same four. alembic + FK-check are out of
  per-story scope but MANDATORY at the full close gate.
- **Full nine-command gate at sprint close on final HEAD** — the evidence of record.
- **Clean-container hygiene (2026-07-14(b)):** stop idle dev-DB / DynamoDB-Local containers before
  the full gate so only the gate's own container runs. NOTE: once STORY-080 lands, its
  contention-hardening should make this hygiene step defensive rather than load-bearing.

## Preconditions (to verify at lock, per edge-case #1)

- Working tree clean on `main` (currently: one untracked `report-2026-07-15-*.html`, unrelated —
  will confirm it is not staged; not a code change).
- Green nine-command DoD baseline on `main` via `yt_gate.py` (idle containers stopped first). If
  the baseline itself trips the `test_dev_db_*` false-red, that is the exact standing problem
  STORY-080 fixes — prove it per the 2026-07-06 protocol and proceed; the sprint branch forks from
  the same `main` HEAD regardless.
- Branch `sprint-47` cut from `main`; start commit tagged `sprint-47-start`.

## Verified contracts (for the subagent briefs — from source + sprint-46 plan)

Confirmed by scout inventory (2026-07-15) + the sprint-46 plan's landed constants:

- **ObservationRepository port** (`backend/src/core/ports/observation_repository.py:26-47`):
  `save_new(batch: Sequence[SignalObservation]) -> int` (idempotent persist, returns count newly
  inserted) and `in_window(signal_key: str, since: datetime, until: datetime) ->
  Sequence[SignalObservation]` (half-open range read).
- **Postgres semantics STORY-084 ports** (`backend/src/adapters/persistence/observation_repository.py:50-128`):
  `save_new` = `INSERT ... ON CONFLICT (source_event_id) DO NOTHING RETURNING` (uniqueness on
  `source_event_id` ALONE; return = true count of newly inserted); `in_window` = half-open
  `[since, until)` on `(signal_key, observed_at)`.
- **Approved DynamoDB observation port** (STORY-084 Context): per observation one
  `TransactWriteItems` — data item (`SIG#<key>` / `<observed_at>#<event_id>`) + dedupe marker
  (`EVT#<event_id>` / `DEDUPE`) with `attribute_not_exists`; cancelled txn = duplicate = not
  counted. `in_window` = Query `pk = SIG#<key> AND sk BETWEEN :since AND :until` with bare-ISO
  bounds (half-open falls out of lexicographic order: `since` < `since#<id>`; `until#<id>` >
  bare `until`), looping on `LastEvaluatedKey`.
- **Postgres semantics STORY-085 ports** (`proposal_repository.py`): `create_open` = partial unique
  index (`WHERE state='open'`) via `ON CONFLICT DO NOTHING` — at most one OPEN per component;
  conflict returns None (the `DecideService` NOOP degrade path, decide.py). `resolve` =
  `UPDATE ... WHERE id=:id AND state='open'`; rowcount≠1 → `ProposalNotOpenError`. IDs = BIGINT
  autoincrement → ported as atomic `COUNTER`/`proposal` item (`UpdateItem ADD seq 1`) so
  the domain field `StatusProposal.id: int | None` is untouched (the counter assigns an
  int on create; the field is Optional and `DecideService` guards with `assert opened.id
  is not None` at `decide.py:138` — plan-verifier item 7, 2026-07-15).
- **Approved DynamoDB proposal item shapes** (STORY-085 Context): `PROPOSAL#<id>`/`META` (sparse
  `gsi1pk=PROPOSAL_OPEN` while open); slot item `COMPONENT#<cid>`/`OPEN_PROPOSAL` (denormalized
  open-proposal copy; safe — open proposals immutable until resolved, slot dies at resolution);
  events `PROPOSAL#<id>`/`EVENT#<occurred_at>#<action>`. `record_approval_event` sets
  `approved_actor` on META when action=approved (consumed by STORY-086).
- **Canonical timestamp format** (sprint-46 constant): UTC only,
  `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` — offset always `+00:00` (never `Z`), microseconds ALWAYS
  padded to 6 digits so lexicographic order == chronological order. Serde lives in
  `backend/src/adapters/persistence/dynamo_serde.py` (landed STORY-083) — STORY-084/085 reuse it.
- **Consistency rule** (sprint-46 constant): decision-path point reads use `ConsistentRead=True`;
  DynamoDB-Local is always consistent, so the AC verifies via a call-kwargs spy.
- **Landed test harness** (`backend/tests/conftest.py`): `dynamo_local` (session-scoped, yields a
  `DynamoPlan`), `clean_dynamo_tables` (function-scoped drop+recreate), `dynamo_resource` (chained,
  yields a boto3 resource). Adapter tests run against the real DynamoDB-Local container — no mocked
  boto3, matching STORY-083's parity approach.

## Story plans

See the per-story sections below. Each will be expanded into TDD steps (RED→GREEN→commit) at the
story's turn; the AC (verbatim in each story file) is the contract, the reviewers judge against it,
not against this plan.

### STORY-080 — dev_db harness: kill the standing gate false-red (5 pts)
Story: `docs/scrum/stories/STORY-080-dev-db-cli-port-collision.md` (AC1–AC5 verbatim there).
Two prongs: (1) collision-proofing `test_dev_db_cli.py` — free scratch port + unique container
name at test time, reusing `scripts/dev_db.py`'s `_free_tcp_port()` / `unique_container_name()`
(both already exist); (2) contention-hardening the shared readiness/connection path so a
healthy-but-busy container's transient "server closed the connection" is retried-until-ready within
a bounded budget (honoring `DEV_DB_READY_TIMEOUT_SECONDS`), not misread as failure. No test skipped,
xfailed, or deleted — the teardown-on-failure and idempotent-against-leftover contracts keep asserting.
Reality gate: run the canonical `pytest` with an unrelated Postgres container pre-bound to 55433 —
the CLI tests pass, not skip.

### STORY-084 — DynamoDB observation adapter (5 pts)
Story: `docs/scrum/stories/STORY-084-dynamodb-observation-adapter.md` (AC1–AC7 verbatim there).
Implement `DynamoObservationRepository` satisfying `ObservationRepository` with exact parity, proven
against `dynamo_local`. Key risks the reviewers + verifier watch: the cross-attribute idempotency
case (AC1 — same `source_event_id`, different `observed_at`, which a same-partition collision would
NOT catch); the half-open boundary (AC3 — exactly `since` included, exactly `until` excluded); real
pagination across `LastEvaluatedKey` (AC4 — forced via Query `Limit`); and the availability-parity
AC6 (identical `AvailabilityResult` — availability%, completeness%, all five counts — whether served
by the Postgres or DynamoDB adapter over a canonical multi-location fixture). Not wired into
composition (AC7).

### STORY-085 — DynamoDB proposal adapter (5 pts)
Story: `docs/scrum/stories/STORY-085-dynamodb-proposal-adapter.md` (AC1–AC6 verbatim there).
Implement `DynamoProposalRepository` satisfying `ProposalRepository`, proven against `dynamo_local`.
Key risks: the one-open-per-component TransactWriteItems (AC1 — META + slot both
`attribute_not_exists`; second create returns None, nothing written); strictly-increasing unique
counter IDs via `UpdateItem ADD` (AC2); the resolve guard's atomicity (AC3 — transition + GSI
strip + slot delete atomic; missing/terminal → `ProposalNotOpenError`, nothing mutated); and the
full decide→approve lifecycle through the REAL `DecideService` + `ApprovalService` behaving
identically to the Postgres run (AC5 — PROPOSED→APPROVED, commit-first publish ordering), with
`approved_actor` denormalized onto META for STORY-086. Not wired into composition (AC6).
