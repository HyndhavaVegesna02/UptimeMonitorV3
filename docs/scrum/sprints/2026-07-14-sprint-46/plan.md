# Sprint 46 Plan — DynamoDB persistence seam + first adapters

**Status:** READY (Updated by Antigravity following yt-plan-verifier output)
**Sprint goal:** Stand up the DynamoDB persistence seam — table bootstrap, throwaway-local
test fixture, settings, boto3 factory — and prove port-contract parity with the first four
adapters (signals, components, watermarks, sample-mode), all without touching the Postgres
wiring.

**Mode:** in-process (default — yt-implementer per story; 082 is 3+ pts so spec + quality
reviewers run concurrently after implementation; 083 is 3 pts so the same applies).

**Stories (8 pts committed — velocity reference: recent sprints 5–8):**
1. STORY-082 — DynamoDB persistence foundation (5 pts)
2. STORY-083 — DynamoDB adapters: signals, components, watermarks, sample-mode (3 pts)

**Execution order + reasoning:** 082 → 083, a hard dependency (083's tests run against
082's `dynamo_local` fixture and 082's `create_tables.py` schemas). 082 also carries the
sprint's risk concentration (Docker lifecycle + port allocation — the same class of machinery
behind STORY-080's flake history), so it goes first while the session is fresh.

**Tooling gaps:** none. Docker 28.5.2 is present (used today by `dev_db.py`); `boto3`
installs from pip; no new MCP/CLI needed. `cfn-lint` is NOT needed this sprint (it joins
the DoD at STORY-088).

**Preconditions (verified at lock, per edge-case #1):** working tree clean on main
(confirmed 2026-07-14 — the STORY-017 spike is stashed; only this plan file is new) and a
green nine-command DoD baseline on main via `yt_gate.py` (idle dev-DB containers stopped
first, per the 2026-07-14(b) clean-container amendment) BEFORE the sprint branch is cut.
A red baseline makes "restore green baseline" the mandatory first story.

**Postgres stays fully wired.** Nothing in this sprint edits `composition/app.py`,
`composition/run.py`, the Postgres adapters, or migrations. The six existing DoD gate
commands remain the gate; the DoD amendment is pending until STORY-087/088 (see the
PENDING AMENDMENT note in `.scrum/definition-of-done.md`).

---

## Design constants (authoritative for both stories — from the PO-accepted 2026-07-14 plan)

| Constant | Value |
| --- | --- |
| Observations table name (default) | `uptime-observations` |
| Control table name (default) | `uptime-control` |
| Key attributes | `pk` (S) / `sk` (S); control-table GSI: `gsi1pk` (S) / `gsi1sk` (S), name `gsi1`, projection ALL |
| Billing | PAY_PER_REQUEST (both tables) |
| Env vars (new, all optional) | `AWS_REGION` (default `us-east-1`), `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE` (defaults above), `DYNAMO_ENDPOINT_URL` (default None = real AWS) |
| Topology items (control table) | `pk="TOPOLOGY"`, `sk="APP#<id>"` / `"COMPONENT#<id>"` / `"SIGNAL#<signal_key>"` |
| Watermark items | `pk="WATERMARK#<signal_key>"`, `sk="META"`, attr `watermark` (canonical ISO string) |
| Sample-mode item | `pk="CONFIG"`, `sk="SAMPLE_MODE"`, attr `enabled` (BOOL); **absent item ⇒ disabled** |
| Canonical timestamp format | UTC only; `YYYY-MM-DDTHH:MM:SS.ffffff+00:00` — offset always spelled `+00:00` (never `Z`), microseconds ALWAYS padded to 6 digits (lexicographic order == chronological order). Parse back to tz-aware UTC (core validators reject naive datetimes). |
| Consistency rule | Decision-path point reads (`WatermarkRepository.get`, `ComponentRepository.get`, `SampleModeRepository.is_enabled`) use `ConsistentRead=True`. |
| DynamoDB Local image | `amazon/dynamodb-local` (container port 8000 → free host port, `-inMemory`) |
| Local credentials | When `DYNAMO_ENDPOINT_URL` is set, the boto3 resource is built with dummy static credentials (`test`/`test`) — DynamoDB Local accepts any; boto3 requires some. Never read real AWS creds for a local endpoint. |

## Verified contracts (probe evidence)

- **Ports being implemented (STORY-083)** — signatures verbatim from `backend/src/core/ports/`:
  - `signal_repository.py::SignalRepository` — `list_signals() -> list[Signal]` (ordered by
    `signal_key`, `[]` if none, never raises); `get(signal_key: str) -> Signal | None`.
  - `component_repository.py::ComponentRepository` — `list_components() -> list[Component]`;
    `get(component_id: str) -> Component | None`; `set_status(component_id: str, status:
    ComponentStatus) -> None` raising `ComponentNotFoundError` when the id does not exist
    (never a silent no-op, never bare ValueError).
  - `watermark.py::WatermarkRepository` — `get(signal_key: str) -> datetime | None`;
    `advance(signal_key: str, to: datetime) -> None`.
  - `sample_mode_repository.py::SampleModeRepository` — `is_enabled() -> bool` (False when
    never set); `set_enabled(enabled: bool) -> None` (idempotent upsert).
- **Domain types consumed** — `Signal(signal_key, name, component_id: str|None,
  interval_seconds: int|None)` (`core/domain/topology.py`); `Component(id, name, status:
  ComponentStatus, app_id)` (`core/domain/component.py`); `ComponentStatus` 4-value enum
  (`core/domain/status.py`). All domain datetimes validated tz-aware UTC.
- **Settings shape being extended (STORY-082)** — `composition/settings.py:38-44`
  (`Settings(database_url, config_dir)` frozen dataclass) and `:46-56` (`load_settings`
  raises `KeyError` when `DATABASE_URL` unset). New fields are ADDITIVE; the KeyError
  behavior and both existing fields are untouched (existing settings tests must keep
  passing unmodified).
- **Fixture ladder being mirrored** — `backend/tests/conftest.py:24-78`
  (`provide_migrated_db`: (1) reuse externally-set env, (2) else spawn throwaway Docker
  container with finalizer teardown even on test failure — proven by a `.throw()` test,
  (3) else `pytest.skip`, plus save/restore of the env vars it reflects into `os.environ`);
  `:81-109` (`clean_runtime_tables` function-scoped isolation precedent); `:112-127`
  (`engine` fixture precedent). The port-allocation + container helpers to mirror live in
  `scripts/dev_db.py` (`resolve_db` / `start_container` / `stop_container`).
- **Postgres adapter behavior being matched (STORY-083 parity scenarios)** — from
  `backend/src/adapters/persistence/`: signal repo is read-only, `SELECT ... ORDER BY
  signal_key`; component `set_status` is a conditional UPDATE with
  `rowcount == 0 → ComponentNotFoundError`; watermark `advance` is an upsert
  (`ON CONFLICT DO UPDATE`), `get` normalizes tz to UTC; sample-mode `is_enabled` returns
  False when the single pinned row is absent, `set_enabled` upserts. Existing test
  scenarios to mirror live in FOUR files (verified 2026-07-14 — the shared assertion
  bodies for signals, sample-mode, and `set_status` are NOT in the adapters file):
  `backend/tests/test_signal_repository_contract.py::_assert_signal_repository_contract`,
  `backend/tests/test_sample_mode_repository_contract.py::_assert_sample_mode_repository_contract`,
  `backend/tests/test_component_repository_contract.py::_assert_set_status_contract`,
  and `backend/tests/test_persistence_adapters.py` (watermark scenarios + component
  list/get only; its `engine` fixture chain is at `conftest.py:112-127`).
- **AC4 scope note (boto3 confinement)** — AC4's "nothing outside `adapters/persistence/`
  + `composition/` imports boto3" governs the backend `src` zones (what import-linter
  covers). Repo-root `scripts/` and `backend/tests/` legitimately import boto3, exactly
  as `scripts/dev_db.py` imports psycopg today while psycopg is forbidden in core —
  established precedent, and the spec review reads AC4 with this scope.
- **Import-linter contracts today** — `core-independence` and `api-outward-independence`
  in `pyproject.toml` forbid `sqlalchemy`/`httpx`/`psycopg` but NOT `boto3` (verified: 0
  boto3 matches in pyproject.toml). Step 082.8 extends both `forbidden_modules` lists with
  `boto3` — the contract COUNT stays 8 (AC5), and the extension is green because no
  core/api module imports boto3.
- **pyproject state** — `boto3` is NOT currently a dependency (the uncommitted STORY-017
  spike that had added it was stashed 2026-07-14); step 082.1 adds it.

---

## STORY-082 — DynamoDB persistence foundation (5 pts)

Story file: `docs/scrum/stories/STORY-082-dynamodb-persistence-foundation.md` (AC verbatim
there; AC1 bootstrap idempotency, AC2 fixture ladder, AC3 settings, AC4 factory,
AC5 boundaries/gates).

- [x] 082.1 Add `boto3` to `[project] dependencies` in `pyproject.toml`;
      `.venv/Scripts/python.exe -m pip install -e ".[dev]"`; sanity `python -c "import
      boto3"`. Commit (chore step — no test precedes a bare dependency add).
- [ ] 082.2 RED: settings tests — with none of the four env vars set, `load_settings()`
      yields `aws_region == "us-east-1"`, the two default table names, `dynamo_endpoint_url
      is None`; with all four set, the overrides win; `DATABASE_URL` still required
      (KeyError test unchanged). GREEN: add the four fields to `Settings` +
      `load_settings`. Commit.
- [ ] 082.3 RED: unit tests for `scripts/dynamo_local.py` resolve ladder (pure logic,
      Docker probed via injected/monkeypatched check, mirroring dev_db's testing style):
      env `DYNAMO_ENDPOINT_URL` set → `source="env"`; else Docker → `source="container"`
      with a free host port; else `source="skip"`. GREEN: implement `resolve_dynamo()`,
      `start_container()` (runs `amazon/dynamodb-local` with `-inMemory`, waits ready),
      `stop_container()` — free-port allocation mirroring `scripts/dev_db.py`. Commit.
- [ ] 082.4 conftest: `provide_dynamo_local()` generator + session-scoped `dynamo_local`
      fixture — mirrors `provide_migrated_db` exactly: reflect `DYNAMO_ENDPOINT_URL` into
      `os.environ` with save/restore, finalizer stops the container even on failure.
      RED first: the `.throw()` teardown-contract test (same pattern the migrated_db
      fixture has). GREEN: implement. Commit.
- [ ] 082.5 RED: `scripts/create_tables.py` tests against `dynamo_local` — creates both
      tables with the exact key schemas + `gsi1` (assert via `DescribeTable`); running it a
      SECOND time completes exit-0 with no error and no schema change (AC1 idempotency);
      CLI entry honors the settings env vars. GREEN: implement (create, wait ACTIVE,
      swallow `ResourceInUseException` on re-run). Commit.
- [ ] 082.6 conftest: function-scoped `clean_dynamo_tables` (delete both tables if present,
      re-create via `create_tables` — full isolation per test on a reused endpoint,
      mirroring `clean_runtime_tables`' role) + `dynamo_resource` fixture (analog of
      `engine` at conftest.py:112-127, chained on `clean_dynamo_tables`). Commit.
- [ ] 082.7 RED: `composition/dynamo.py::make_dynamo_resource(settings)` test — with
      `dynamo_endpoint_url` set, the resource targets the local endpoint with dummy creds
      and a PutItem/GetItem round-trips on a bootstrapped table; region honored. GREEN:
      implement. Commit.
- [ ] 082.8 Extend pyproject.toml contracts: add `boto3` to the `forbidden_modules` list for `core-independence` and `api-outward-independence`. Verify the contract count stays 8. Commit.
- [ ] 082.9 Boundary + gate: `importlinter` green (boto3 usage confined to
      `adapters/persistence`—none yet—and `composition`, `scripts/`, tests); scoped story
      gate `yt_gate.py --only` {pytest, ruff check, ruff format, importlinter} — the four
      commands this diff can affect (no migration/schema change ⇒ alembic + FK check are
      out of scope per the 2026-07-14(a) token-economy amendment). Wiki blast-radius check: `yt_wiki.py` sweep for `pyproject.toml` (e.g. `architecture-boundary.md`) and `conftest.py` (e.g. `dev-setup-and-dod.md`, `migrations-and-db.md`, `persistence-adapters.md`), updating/re-verifying as needed. Tick board, reviews
      (spec ∥ quality), reality-gate note: this story's live surface IS the local fixture
      path (no vendor path exists yet); the container-spawn path must run for real in the
      test session, not only mocked — evidence = the pytest output showing container
      lifecycle tests executed (not skipped) on this machine.

## STORY-083 — DynamoDB adapters: signals, components, watermarks, sample-mode (3 pts)

Story file: `docs/scrum/stories/STORY-083-dynamodb-topology-adapters.md` (AC verbatim
there; AC1 signals, AC2 components, AC3 watermarks, AC4 sample-mode, AC5 boundaries).

- [ ] 083.1 RED: unit tests for `adapters/persistence/dynamo_serde.py` — canonical
      serialization (zero-microsecond datetime pads to `.000000`; offset renders `+00:00`;
      naive datetime rejected; parse(serialize(dt)) == dt; lexicographic order of two
      serialized instants matches chronological order across the microsecond-padding
      boundary). GREEN: implement `to_canonical_iso` / `from_canonical_iso`. Commit.
      (STORY-084 reuses this module — it is shared infrastructure, name it accordingly.)
- [ ] 083.2 RED: `DynamoSignalRepository` contract tests against `dynamo_resource` —
      empty table → `[]`; three seeded signal items return ordered by `signal_key`; field
      fidelity incl. `component_id=None` / `interval_seconds=None` absent-attr handling;
      `get` miss → None. GREEN: implement (Query `pk="TOPOLOGY" AND begins_with(sk,
      "SIGNAL#")`; GetItem for `get`). Commit.
- [ ] 083.3 RED: `DynamoComponentRepository` tests — `list_components` / `get` fidelity;
      `get` uses ConsistentRead (verify via call-kwargs spy, as DynamoDB-Local is always consistent);
      `set_status` flips the attr; `set_status` on a missing id raises
      `ComponentNotFoundError` (ConditionalCheckFailed mapped, nothing written). GREEN:
      implement (UpdateItem with `attribute_exists(pk)` condition… full key condition on
      pk+sk). Commit.
- [ ] 083.4 RED: `DynamoWatermarkRepository` tests — `get` on never-advanced → None;
      `advance` then `get` round-trips the exact instant tz-aware UTC (via dynamo_serde);
      `advance` twice = upsert (last write wins); `get` uses ConsistentRead (verify via call-kwargs spy). GREEN:
      implement. Commit.
- [ ] 083.5 RED: `DynamoSampleModeRepository` tests — `is_enabled()` False on absent item;
      `is_enabled` uses ConsistentRead (verify via call-kwargs spy);
      `set_enabled(True)` → True; setting the same value again succeeds silently;
      toggle round-trips. GREEN: implement. Commit.
- [ ] 083.6 Parity sweep: mirror each relevant scenario from
      `backend/tests/test_persistence_adapters.py` for these four ports (scenario-for-
      scenario in `test_dynamo_adapters.py` — separate file, no parametrizing the Postgres
      suite over two backends: that would double DB spin-ups and violate the
      one-DB-gated-run-at-a-time rule). Confirm composition wiring untouched
      (`git diff` shows no `composition/app.py`/`run.py` change — AC5). Commit.
- [ ] 083.7 Scoped story gate (same four commands as 082.9); wiki blast-radius check
      (`yt_wiki.py` — new files carry no `code_refs` yet, but `pyproject.toml` and
      `conftest.py` are cited by existing articles; any hit gets updated or re-verified);
      reviews (spec ∥ quality); board to done.

## Sprint-close obligations

- FULL nine-command gate (the evidence of record) on the final sprint HEAD — clean tree,
  idle dev-DB containers stopped first (2026-07-14(b) clean-container amendment).
- Wiki compile pass (`yt_wiki.py` exit 0) before review; new wiki article or update for the
  DynamoDB persistence seam is expected fallout of 082/083's learnings.
- Reality-gate evidence recorded per story (082: real container lifecycle executed in-session;
  083: contract parity suite green against a real local DynamoDB — no mocked boto3 in the
  adapter tests).
