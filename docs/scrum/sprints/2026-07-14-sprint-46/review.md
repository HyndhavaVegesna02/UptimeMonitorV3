# Sprint 46 Review — DynamoDB persistence seam + first adapters

**Goal:** Stand up the DynamoDB persistence seam (table bootstrap, throwaway-local test
fixture, settings, boto3 factory) and prove port-contract parity with the first four
adapters (signals, components, watermarks, sample-mode), without touching Postgres wiring.

**Committed:** 8 points — STORY-082 (5) + STORY-083 (3). Both Done, pending PO acceptance.

## Execution note — planned in-process, delivered external

The CC session limit was hit mid-sprint. The PO pivoted to external implementation via
Antigravity (22 `(Antigravity)` commits on `sprint-46`). On resume, the orchestrator
verified the work under YourTeam **external-mode** rules — spec + quality review per story
regardless of size, plus an independent full-gate re-run — before either story's Done
stood. The board's `mode: in-process` records the plan; this section records the reality.
(Retro input: external delivery + the review floor caught one MAJOR that self-review missed.)

## STORY-082 — DynamoDB persistence foundation (5 pts)

**Built:** `scripts/create_tables.py` (idempotent two-table + GSI1 bootstrap),
`scripts/dynamo_local.py` + the `dynamo_local`/`clean_dynamo_tables`/`dynamo_resource`
pytest fixtures (real `amazon/dynamodb-local` container, skip-if-no-Docker ladder,
teardown-on-failure), four additive `Settings` fields (`aws_region`, two table names,
endpoint override — `DATABASE_URL` KeyError preserved), and
`composition/dynamo.py::make_dynamo_resource` (dummy creds only for a local endpoint).
`boto3` added to deps and to the `core-independence` + `api-outward-independence`
forbidden lists (contracts stay at 8). Postgres left fully wired.

**Reviews:**
- Spec — **PASS**. All 5 AC traced to real tests; AC1 idempotency, AC2 teardown-on-failure,
  AC4 boto3 round-trip all run against a real container (confirmed not skipped). No gaps.
- Quality — **FIX_REQUIRED → FIXED**. One MAJOR: `test_provide_dynamo_local_teardown_on_failure`
  forced the real container-spawn path via monkeypatched `docker_available=True` with no
  skip guard, so bare `pytest` would ERROR (not skip) on a no-Docker machine — breaking the
  AC2 skip-ladder invariant. **Fixed in `6c4a257`** with a collection-time
  `@pytest.mark.skipif(not dynamo_local.docker_available(), …)`, mirroring the sibling
  `test_dev_db_fixture.py` guard. Verified: file's 7 tests pass, ruff clean.

**Minors captured (non-blocking — candidate cleanup follow-up):**
1. `scripts/dynamo_local.py` `docker_available()`/`_free_tcp_port()` are verbatim copies of
   `scripts/dev_db.py` — defensible only because the Postgres harness retires at cutover
   (STORY-087); a shared helper is worth it if both survive.
2. `scripts/create_tables.py::main()` injects an unrestored dummy `DATABASE_URL` to satisfy
   `load_settings()` — couples the DynamoDB bootstrap to the Postgres settings requirement.
3. Stale `try/except ImportError` TDD scaffolding + now-false comments in
   `test_create_tables.py` and `test_dynamo_composition.py`.
4. Formatting-only edit to the shared `.claude/skills/yourteam/scripts/yt_wiki.py` (skill-dir
   drift riding in on a feature story) — acceptable once, flagged so it doesn't recur.

## STORY-083 — DynamoDB adapters: signals, components, watermarks, sample-mode (3 pts)

**Built:** `dynamo_serde.py` (canonical fixed-width ISO-UTC, `+00:00` spelling, 6-digit
microsecond padding, naive-datetime rejection) + four adapters, each taking
`db_resource, table_name: str` (the 083.6 boundary fix that keeps adapters-edge-only green).
`ConsistentRead=True` on exactly the three decision-path reads (`component.get`,
`watermark.get`, `sample_mode.is_enabled`); `set_status` uses `attribute_exists(pk)` →
`ComponentNotFoundError` (faithful port of the Postgres rowcount-0 guard). Not wired into
composition (STORY-087 does the cutover).

**Reviews:**
- Spec — **PASS**. All 5 AC traced; signal/component contracts reuse the SAME shared
  assertion bodies the Postgres/fake adapters run (real parity); the three ConsistentRead
  spy-tests genuinely assert the kwarg; `git diff` confirms `composition/app.py`/`run.py`
  untouched. No gaps.
- Quality — **APPROVE**. 0 critical, 0 major. Tests run against a real DynamoDB Local
  container (no moto/mocks); serde correctness and key-schema strings verified against the
  design constants; wiki updates accurate with in-range `verified_sha`.

**Minors captured (non-blocking):**
1. `signal.get()` omits `ConsistentRead` (intentional read-model path, matches the wiki) —
   a one-line comment would prevent it reading as an oversight.
2. `list_signals`/`list_components` don't paginate on `LastEvaluatedKey` — safe at the
   documented tiny-topology scale (<1 MB Query page), latent only if topology ever grows.
3. `test_dynamo_adapters.py::_seed_component_dynamo` annotates `name: str = None`
   (should be `str | None`; test-only nit).

## Definition of Done — evidence of record

Full 9-command gate independently re-run on final HEAD `6c4a257`:
**8/9 green outright** — importlinter (8 contracts kept), check_fk_direction (11 FKs, 0
violations), alembic upgrade head, ruff check, ruff format, npm test (363), npm build,
npm lint. pytest: **598 passed + 1 proven contention false-red**.

**The false-red:** `test_dev_db_fixture.py::test_container_is_torn_down_even_when_a_test_using_the_fixture_fails`
(a Postgres dev-db test — "server closed the connection unexpectedly" under full-suite
Docker pressure). Proven per the 2026-07-06 contention protocol: (1) empty diff for
`test_dev_db_fixture.py` and `scripts/dev_db.py` since `sprint-46-start` — this sprint
never touched the Postgres dev-db harness; (2) passes in isolation (6 passed, exit 0) with
no competing container. This is the STORY-080 flake family (port-collision / connection
disconnect), already PO-prioritized for a durable fix. Every DynamoDB product test passed.
(An earlier full-gate run at 8153b53 tripped a different member of the same family,
`test_dev_db_cli.py`, likewise proven a false-red.)

## Demo / verification

No runtime UI surface this sprint (foundation + not-yet-wired adapters, per design). The
live surface is the test path: the adapter contract suite executes against a **real**
DynamoDB Local container — 15 DynamoDB tests green, reusing the same contract-assertion
bodies as the Postgres adapters, proving cross-backend parity. Reality gate satisfied:
container lifecycle (spawn + teardown-on-failure) exercised for real, adapters verified
against real DynamoDB, no mocked boto3 in the adapter tests.

## Recommendation

Both stories meet their AC with passing spec + quality reviews and a green gate (modulo the
proven, pre-existing dev-db false-red). **Recommend ACCEPT of STORY-082 and STORY-083**
(8 points). On acceptance the branch merges to main. The captured minors are candidates for
a small cleanup follow-up story (or fold into STORY-087's cutover, which already retires
half of them). STORY-080's durable dev-db-flake fix is reaffirmed by this sprint's gate.
