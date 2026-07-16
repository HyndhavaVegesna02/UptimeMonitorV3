# Sprint 49 — Plan

**Goal:** Complete the AWS cutover: wire the DynamoDB adapter set into both composition
roots and delete the entire Postgres stack (STORY-087), containerize both processes in
one image (STORY-092), and author the CloudFormation single-stack template + console
deployment runbook (STORY-088) — so the system runs on DynamoDB, builds as a container,
and is one PO-driven console session away from living on AWS.

**Mode:** `external` — the PO implements via an external AI agent building to THIS plan
alone. `plan.md` is the full contract (self-contained; edge behavior explicit; exact
symbols and signatures cited). The orchestrator does planning, board-keeping, and
post-implementation verification: **yt-spec-reviewer + yt-quality-reviewer per story
regardless of points**, plus an independent `yt_gate.py` re-run on the final HEAD, plus
the reality gate, before any story goes `board: done`.

**Stories (10 pts):**

| Order | Story | Pts | Why here |
| ----- | ----- | --- | -------- |
| 1 | STORY-087 — Composition cutover to DynamoDB; retire Postgres; DoD amendment lands | 3 | Dependency + highest blast radius. Everything downstream builds on the DynamoDB-only runtime and the amended gate. Deletes the most code. |
| 2 | STORY-092 — Containerize both processes (single Dockerfile, CMD override) | 2 | Depends on 087: the image must be built against the DynamoDB-only runtime (no psycopg, no `DATABASE_URL`). Produces the ECR artifact 088 references. |
| 3 | STORY-088 — CloudFormation single-stack template + console runbook; `cfn-lint` joins DoD | 5 | Depends on both: references the container image (092) and the amended gate set (087); adds `cfn-lint`. |

**Execution order reasoning:** pure dependency chain 087 → 092 → 088, which also happens
to be risk-first (087 is the irreversible-feeling deletion + gate flip) and
size-ascending only incidentally. **Drop order if delivery runs long:** 088 first (last,
largest, and the only story with no downstream dependant this sprint), then 092. 087
never drops — it unblocks the other two and is the epic's load-bearing slice.

**Delivery contract (external mode — stated at handoff, verified on return):**
1. **Commit per story, not one lump.** Each story is its own commit(s) with `STORY-NNN:`
   messages on `sprint-49`, ideally the per-green-step TDD cadence. If work returns as one
   uncommitted tree, the orchestrator reads each diff and commits per story BEFORE
   reviewing.
2. **Never trust a self-reported gate.** "All gates green" is a to-verify list. The
   orchestrator's own `yt_gate.py` run on the final HEAD is the only record that counts —
   and it must run with **DynamoDB Local up** (see §Gate note) so the persistence suite
   actually executes rather than skips.
3. The external agent works ONLY on `sprint-49`; it never merges to main.
4. Reviewers get each story's own commit range as their primary object.

**Tooling gap (second of the two allowed change moments — planning):**
`cfn-lint` is NOT installed (`python -m cfnlint --version` → "No module named cfnlint").
STORY-088 AC2 requires it in the gate. **Install `cfn-lint` into the venv before STORY-088
begins** (`.venv/Scripts/python.exe -m pip install cfn-lint`, and add `cfn-lint` to the
`[project.optional-dependencies].dev` list in `pyproject.toml`). DynamoDB Local is already
available (STORY-082: `scripts/dynamo_local.py` + the `dynamo_local` fixture). `boto3` and
`python-dotenv` are already runtime deps.

**Plan-verifier:** DISPATCHED — this sprint is contract-sensitive on every axis
(adapter/vendor wiring in 087, a vendor CloudFormation template in 088, and `external`
mode makes plan.md the full contract). Verdict + GAP resolution recorded at the bottom of
this file. Must reach LOCK_READY before the PO sees the plan.

---

## Verified API contracts (cited from producing code @ b16fb58)

These are the exact symbols the cutover consumes. All line numbers are current HEAD.

### DynamoDB resource factory — `backend/src/composition/dynamo.py:10`
```python
def make_dynamo_resource(settings: Settings):  # returns a boto3 dynamodb ServiceResource
```
Reads `settings.aws_region`; when `settings.dynamo_endpoint_url` is set, targets local
DynamoDB with dummy `test`/`test` creds. **This is the ONE home for building the resource;
both composition roots call it — never re-implement the boto3 kwargs.**

### Settings — `backend/src/composition/settings.py:38-66`
Existing DynamoDB fields (already present, STORY-082): `aws_region` (default
`"us-east-1"`), `dynamo_observations_table` (default `"uptime-observations"`),
`dynamo_control_table` (default `"uptime-control"`), `dynamo_endpoint_url` (`str | None`).
Read from env: `AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`,
`DYNAMO_ENDPOINT_URL`. **STORY-087 removes the `database_url` field, the
`APP_DATABASE_URL_VAR`/`os.environ["DATABASE_URL"]` read at line 58, and `to_psycopg_url`.**

### DynamoDB adapter constructors — all take `(db_resource, table_name: str)`
`backend/src/adapters/persistence/dynamo_*_repository.py`. **Table assignment is a hard
contract, verified from the landed adapter tests:**

| Repository class | Table (settings field) |
| ---------------- | ---------------------- |
| `DynamoObservationRepository` | `dynamo_observations_table` |
| `DynamoRejectedObservationRepository` | `dynamo_control_table` |
| `DynamoSignalRepository` | `dynamo_control_table` |
| `DynamoComponentRepository` | `dynamo_control_table` |
| `DynamoWatermarkRepository` | `dynamo_control_table` |
| `DynamoProposalRepository` | `dynamo_control_table` |
| `DynamoPublicationRepository` | `dynamo_control_table` |
| `DynamoMaintenanceRepository` | `dynamo_control_table` |
| `DynamoSampleModeRepository` | `dynamo_control_table` |

**Only the observation repository uses the observations table. Everything else — rejected
observations included — uses the control table.** (Evidence: `test_dynamo_observation_repository.py:66-67`
observations; `test_dynamo_rejected_observation_repository.py:14-15` control; the rest in
`test_dynamo_adapters.py` / `test_dynamo_*_repository.py` control.)

### DynamoDB topology seed — `backend/src/composition/seed_dynamo.py:13`
```python
def seed_topology_dynamo(config: Config, db_resource, table_name: str) -> None
```
`table_name` is the **control** table. Idempotent upsert; preserves existing component
`status` (only sets `OPERATIONAL` default via `if_not_exists`). Replaces the Postgres
`seed_topology(config, engine)` at both roots.

### Table bootstrap — `scripts/create_tables.py:21`
`create_tables()` reads settings and creates both tables (observations: pk/sk;
control: pk/sk + `gsi1` GSI). `main()` at lines 100-105 has a dummy-`DATABASE_URL`
guard (101-103) that STORY-087 removes once `load_settings` no longer requires it.

### Grail executor (unchanged) — `backend/src/adapters/inbound/dynatrace/grail_executor.py`
`make_grail_executor(env_url=..., api_token=...)` — the live loop keeps this as-is.

---

## STORY-087 — Composition cutover to DynamoDB (3 pts)

**Full AC:** see `docs/scrum/stories/STORY-087-dynamodb-cutover.md` (AC1 wiring, AC2
retirement, AC3 DoD amendment, AC4 e2e proof, AC5 docs+wiki). Hard cutover — no
dual-read, no data migration (PO decision 2026-07-14).

### Files changed / deleted (exhaustive)

**Rewire (edit):**
- `backend/src/composition/settings.py` — remove `database_url` field (line 42),
  `APP_DATABASE_URL_VAR` (20), the `os.environ["DATABASE_URL"]` read (58), and
  `to_psycopg_url` (23-35). Rewrite the module docstring (currently all-Neon) to describe
  the DynamoDB settings. `Settings` keeps `config_dir` + the four dynamo fields. Leave
  `LiveSecrets`/`StatuspageSecrets`/`load_*_secrets` untouched.
- `backend/src/composition/app.py` — in `create_app`, replace the Postgres branch
  (lines 73-122: the `import sqlalchemy as sa`, all six `Postgres*Repository` imports,
  `create_engine`, and construction) with DynamoDB wiring: `settings = load_settings()`;
  `db_resource = make_dynamo_resource(settings)`; construct each repo with the table per
  the contract table above (proposal/component/maintenance/publication/signal/sample-mode
  → control table; if the approve-trigger path never reads observations, an
  `observation_repo` is still wired for symmetry with the port set → observations table).
  `app.state.db_engine` → replace with `app.state.dynamo_resource = db_resource` (no engine
  concept). Keep the `else` injected-fakes branch behavior (set the resource-state attr to
  `None`). Load + attach `seed_config` from `config_dir` as today.
  Also remove the `from src.composition.seed import seed_topology` import at `app.py:27`
  (replaced by `seed_dynamo`). State the fate of the `database_url` param at `app.py:38`
  (GAP-5): **drop it** from `create_app`'s signature (it becomes meaningless once settings
  has no `database_url`) — and note that endpoint/asgi tests currently passing
  `database_url=migrated_db.database_url` (`test_asgi.py:51`, `test_topology_endpoint.py:194`,
  `test_sample_mode_endpoint.py:148`, and any peers) are **rewritten to inject fakes or the
  `dynamo_resource` fixture — NOT deleted** — so endpoint coverage survives the cutover.
- `backend/src/composition/app.py::lifespan` (lines 20-33) — the boot seed switches from
  `seed_topology(seed_config, db_engine)` to
  `seed_topology_dynamo(seed_config, app.state.dynamo_resource, settings.dynamo_control_table)`;
  gate on `dynamo_resource is not None`. **Remove the `db_engine.dispose()` teardown** — a
  boto3 resource needs no disposal. (Resolve `settings`/control-table name into lifespan
  via `app.state`, e.g. stash `app.state.control_table` at wire time, so lifespan needs no
  fresh `load_settings`.)
- `backend/src/composition/run.py` — replace all `Postgres*Repository` imports (18-37)
  and `import sqlalchemy as sa` (14) with the Dynamo imports + `make_dynamo_resource`.
  **Also remove `to_psycopg_url` from the settings import at `run.py:48`** (inside the
  `from src.composition.settings import (...)` block, 43-49) — it is deleted from
  `settings.py`, so leaving the import is an ImportError on any `import src.composition.run`
  (GAP-4). Remove the `from src.composition.seed import seed_topology` import at `run.py:42`
  (replaced by `seed_dynamo`).
  `build_live_loop`'s signature changes: drop `engine: sa.Engine`, add
  `db_resource` + resolve table names from `settings` (already a param). Wire the seven
  loop repos (observation → observations table; watermark/rejected/maintenance/component/
  proposal/publication + sample-mode → control table) per the contract table. `main()`
  (139-206): replace `to_psycopg_url`+`create_engine` (181-182) with
  `make_dynamo_resource(settings)`; `seed_topology(config, engine)` (187) →
  `seed_topology_dynamo(config, db_resource, settings.dynamo_control_table)`; **remove the
  `finally: engine.dispose()`** (203-205) — no disposal needed. Keep `load_dotenv()`,
  `load_live_secrets`, `check_vendor_id_health` exactly as-is.
- `scripts/create_tables.py` — remove the dummy-`DATABASE_URL` guard in `main` (101-103);
  `load_settings()` no longer requires it.
- `backend/tests/conftest.py` — remove `import dev_db` (21); delete
  `provide_migrated_db`/`migrated_db`/`clean_runtime_tables`/`engine` fixtures (121-225);
  in `provide_dynamo_local` remove the dummy-`DATABASE_URL` save/set/restore (42-44,
  52-55) — settings no longer needs it. Keep the Dynamo fixtures
  (`dynamo_local`/`clean_dynamo_tables`/`dynamo_resource`).

**Delete (record reason in STORY-087 History — DoD standing rule):**
- All nine `Postgres*Repository` adapters:
  `backend/src/adapters/persistence/{component,maintenance,observation,proposal,
  publication,rejected_observation,sample_mode,signal,watermark}_repository.py`
  (only the `Postgres*` classes — the `dynamo_*_repository.py` files stay). If any file
  holds only the Postgres class, delete the file; if shared, delete the class.
- **`backend/src/composition/seed.py`** — the Postgres `seed_topology(config, engine)`
  (imports `sqlalchemy as sa`/`JSONB`/`Engine` at `seed.py:13-15`). Once both roots use
  `seed_topology_dynamo`, this whole file is dead AND breaks the step-4 no-sqlalchemy guard
  and `import src.composition` after the dep removal (GAP-1). Delete the file.
- `alembic.ini` (repo root) and the entire `migrations/` tree (`env.py` + all 8 version
  files).
- `scripts/dev_db.py` and `scripts/check_fk_direction.py`.
- Postgres-only test modules — delete whole: `test_persistence_adapters.py`,
  `test_spine_schema.py`, `test_dev_db_cli.py`, `test_dev_db_fixture.py`, the
  check_fk_direction unit test, and **`test_app.py::test_app_lifespan_disposes_engine`
  (`test_app.py:24-45`)** — the last asserts `db_engine.dispose()`, which lifespan no
  longer does, and it matches NONE of the sweep terms below, so a literal sweep misses it
  (GAP-2): enumerate it explicitly.
- **Surgically de-couple (do NOT delete) the two KEPT Dynamo test files** that carry
  Dynamo-vs-Postgres *parity* tests (GAP-3): from
  `test_dynamo_observation_repository.py` remove the top-level `import psycopg` (`:5`) and
  `PostgresObservationRepository` import (`:9-11`) and the parity test using
  `engine`/`migrated_db` (`:188` ff); from `test_dynamo_proposal_repository.py` remove the
  `PostgresProposalRepository` import (`:7`), the `from tests.test_persistence_adapters
  import seed_component` (`:17` — that module is deleted), and the parity test using
  `engine`/`migrated_db` (`:227` ff). Keep every pure-Dynamo test in both files — they are
  the persistence floor.
- After the above, grep `sqlalchemy`, `psycopg`, `alembic`, `migrated_db`,
  `check_fk_direction`, `dev_db`, `seed_topology` (the Postgres one) under `backend/` and
  confirm zero remaining references outside the archived-history docs.
- `pyproject.toml` — remove `sqlalchemy>=2`, `alembic`, `psycopg[binary]` from
  `[project].dependencies`. Keep `boto3`, `httpx`, `python-dotenv`, `fastapi`, `pydantic`,
  `uvicorn`, etc.

**Deletion reason (record verbatim in the story History):** "Postgres/Alembic/psycopg,
the FK-direction check, the throwaway-DB harness, and the two-URL machinery are superseded
by the DynamoDB persistence zone (STORY-082..086); the composition cutover (STORY-087)
removes the last runtime references, so the code is dead."

### DoD amendment (AC3) — edit `.scrum/definition-of-done.md`
- Remove the `check_fk_direction.py` gate line and the `alembic upgrade head` gate line
  (both currently in "Commands (backend)").
- Convert the PENDING AMENDMENT block (lines 26-33) into an EFFECTIVE note citing "PO
  approval 2026-07-14; landed STORY-087 sprint-49": the persistence floor is now the
  DynamoDB-Local-backed `pytest` suite; `cfn-lint infra/` will join at STORY-088.
- Backend gate set after this story: `pytest`, `lint-imports` (the module-path
  invocation), `ruff check .`, `ruff format --check .`. Frontend unchanged.
- Update CLAUDE.md's Key commands + Database sections to match (AC5).

### AC4 e2e proof (reality gate — orchestrator runs, evidence recorded)
Full local stack on DynamoDB: `scripts/dynamo_local.py` up → `python scripts/create_tables.py`
→ `uvicorn src.composition.asgi:app --port 8000` (boot seed populates the control table)
→ `python -m src.composition.run` (needs Dynatrace/Statuspage secrets in `.env`) →
`cd frontend && npm run dev`. Verify: loop ingests, watermark advances across two cycles,
all six tabs render, one mutation (approve/reject) round-trips. Record evidence in
`sprint-current.yaml.reality_gate`. **If live Dynatrace secrets are unavailable in-session,
this AC cannot ship on promise — split the live-loop portion or block; the API+seed+tabs
half can still be exercised against DynamoDB Local (state that honestly in evidence).**

### AC5 wiki blast radius (must resolve before Done)
Articles whose `code_refs` overlap this diff (from the planning inventory):
- `docs/scrum/wiki/migrations-and-db.md` (refs alembic/migrations/dev_db/check_fk_direction)
  → **archive with a tombstone** (the whole subject is deleted): sprint-49, STORY-087,
  reason "Postgres/Alembic/FK-direction removed at the DynamoDB cutover."
- `docs/scrum/wiki/dev-setup-and-dod.md` (refs dev_db/check_fk_direction/pyproject/conftest)
  → **update**: DynamoDB Local recipe, amended DoD, container-based local stack.
- `docs/scrum/wiki/persistence-adapters.md` (refs both Postgres + Dynamo adapters)
  → **update**: drop the deleted Postgres adapters, re-verify against the Dynamo-only set,
  bump `verified_sha`.
- `docs/scrum/wiki/architecture-boundary.md` (refs check_fk_direction) → **update**: the
  spine→feature FK boundary retires; the core-independence import contract stays the floor.
- Run `python .claude/skills/yourteam/scripts/yt_wiki.py` → exit 0 (link lint; repoint any
  link into the archived article to its tombstone).

### TDD checkbox steps
- [ ] 1. `settings.py`: write a test that `load_settings()` succeeds with ONLY
  `AWS_REGION`/`DYNAMO_*` env set and no `DATABASE_URL`; see it fail; remove `database_url`
  + `to_psycopg_url` + `APP_DATABASE_URL_VAR`; see it pass; commit.
- [ ] 2. `run.py::build_live_loop`: adapt/author a test constructing the loop with a
  DynamoDB resource (via `dynamo_resource` fixture) — asserts loops build, correct repo
  types, no `sa.Engine`; make it green by rewiring; commit.
- [ ] 3. `app.py::create_app`: test the app builds on DynamoDB (real `dynamo_resource`,
  boot seed populates control table, `/api/v1/health` + one read endpoint respond); rewire
  lifespan + wiring; drop engine disposal; commit.
- [ ] 4. Delete the Postgres surface per the "Delete" block above — nine `Postgres*`
  adapters, `composition/seed.py`, `alembic.ini`/`migrations/`,
  `scripts/dev_db.py`/`check_fk_direction.py`, the whole-delete test modules incl.
  `test_app.py::test_app_lifespan_disposes_engine`; **surgically de-couple** the two kept
  Dynamo parity-test files; rewrite endpoint/asgi tests off `database_url=`. Remove the
  three deps from `pyproject.toml`; add a guard test/grep asserting no
  `sqlalchemy`/`create_engine`/`psycopg` under `backend/src`; `pip install -e ".[dev]"`
  clean; commit (record deletion reasons in story History).
- [ ] 5. `conftest.py`: remove `import dev_db` + the four Postgres fixtures + the
  dummy-`DATABASE_URL` reflection in `provide_dynamo_local`; `create_tables.py`: drop the
  dummy guard; full `pytest` green (with DynamoDB Local up); commit.
- [ ] 6. Amend `.scrum/definition-of-done.md` (drop two gates, flip the amendment note);
  `python .claude/skills/yourteam/scripts/yt_gate.py` GREEN under the amended set on a
  clean tree; commit.
- [ ] 7. Rewrite CLAUDE.md Key commands / Database sections for DynamoDB; resolve wiki
  blast radius (archive/update the four articles, bump verified_sha, `yt_wiki.py` exit 0);
  commit.

---

## STORY-092 — Containerize both processes (2 pts)

**Full AC:** see `docs/scrum/stories/STORY-092-containerize-both-processes.md`. Built AFTER
087 so the image carries no Postgres layer.

### Deliverables
- Repo-root `Dockerfile`, `python:3.13-slim` base. Copy `pyproject.toml` + `backend/` +
  `config/`; `pip install .` (runtime deps only, NOT `[dev]`). `WORKDIR` and `PYTHONPATH`
  set so `src` (which lives at `backend/src`, exposed via `package-dir = {"" = "backend"}`)
  imports. `EXPOSE 8000`. Default `CMD ["uvicorn", "src.composition.asgi:app", "--host",
  "0.0.0.0", "--port", "8000"]`. No loop-specific command baked in.
- Loop runs by command override: `python -m src.composition.run` (documented; used by the
  088 loop task definition + runbook).
- `.dockerignore` per AC3 (`.venv/`, `.git/`, `frontend/node_modules/`, `frontend/dist/`,
  `**/__pycache__/`, `backend/tests/`, `.scrum/`, `docs/`, `.claude/`).

### AC4 build + import smoke (reality gate — evidence recorded)
`docker build -t uptime-monitor .` succeeds; `docker run --rm --entrypoint python
uptime-monitor -c "import src.composition.asgi; import src.composition.run"` exits 0.
Record build tail + smoke exit in `sprint-current.yaml`.

### Checkbox steps
- [ ] 1. Author `.dockerignore`; commit.
- [ ] 2. Author `Dockerfile` (base, install, WORKDIR/PYTHONPATH, EXPOSE, default CMD); commit.
- [ ] 3. `docker build` → success; import smoke → exit 0; record evidence; commit any fixups.
- [ ] 4. CLAUDE.md tooling/commands note the Dockerfile + two invocations; wiki blast radius
  (if any); commit.

*Note: `docker build`/`docker run` are the story's reality gate, NOT DoD-gate commands. The
amended `yt_gate.py` set (pytest/lint-imports/ruff ×2 + frontend) still runs and must stay
green — the Dockerfile changes no Python source.*

---

## STORY-088 — CloudFormation single-stack + console runbook (5 pts)

**Full AC + the complete approved resource set:** see
`docs/scrum/stories/STORY-088-cloudformation-stack-runbook.md` (AC1 template, AC2 lint
gate, AC3 loop singleton, AC4 secrets hygiene, AC5 runbook, AC6 gates). The story file's
Context paragraph is the binding resource list — build `infra/stack.yaml` to it exactly.

### Prerequisite (do FIRST): install `cfn-lint`
`.venv/Scripts/python.exe -m pip install cfn-lint`; add `cfn-lint` to
`[project.optional-dependencies].dev` in `pyproject.toml`.

### Key contract points (from the story, not to be re-derived)
- One `infra/stack.yaml`: VPC (2 public subnets / 2 AZs + IGW), SGs (ALB ← CloudFront
  managed prefix list; API 8000 ← ALB SG only; loop no ingress), the **two DynamoDB tables
  with `DeletionPolicy: Retain`** (schema must match `create_tables.py`: observations
  pk/sk; control pk/sk + `gsi1` GSI on `gsi1pk`/`gsi1sk`), one ECR repo, ECS cluster +
  execution role + one task role scoped to the two table ARNs **and the GSI ARN**, two task
  defs (0.25 vCPU / 0.5 GB; api = default image CMD with `/api/v1/health` healthcheck; loop
  = command override `python -m src.composition.run` + the two Secrets Manager secrets),
  two services desiredCount=1, **loop service `minimumHealthyPercent: 0,
  maximumPercent: 100`** (AC3 — double-publish guard), ALB HTTP:80 → api target group,
  private S3 + OAC, CloudFront (default → S3; ordered `/api/*` → ALB, all methods, caching
  disabled; CloudFront Function rewriting extensionless paths → `/index.html` on the
  default behavior ONLY), two log groups (14-day retention), two Secrets Manager secrets
  (NAMES only).
- Outputs: CloudFront domain, ALB DNS, ECR URI, table names.
- Parameters: image tag, desired counts, **and a CloudFront origin-facing prefix-list ID**
  (`pl-…`) — the ALB SG ingress "← CloudFront managed prefix list" has NO CFN
  intrinsic/pseudo-parameter to resolve `com.amazonaws.global.cloudfront.origin-facing`, so
  it must be a template Parameter (region-specific value the runbook tells the PO to look
  up) or a region-locked literal; `cfn-lint` will NOT catch a missing value (GAP-6). The
  runbook lists where the PO obtains the region's prefix-list ID.
- The api task def references the STORY-092 image (default CMD); the loop task def
  overrides CMD to `python -m src.composition.run`.

### Secrets hygiene (AC4) — NO secret value at any commit
Template references Secrets Manager ARNs. The runbook lists every env var + secret NAME per
service (`AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE`; loop also
`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`, `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`) and
where the PO enters each value in-console.

### AC5 runbook — `docs/deploy-runbook.md`
End-to-end console walkthrough assuming no prior AWS knowledge: stack upload/create → secret
value entry → ECR login + image build/push (the one CLI-only step, verbatim commands, using
the STORY-092 Dockerfile) → frontend `npm run build` + S3 upload + CloudFront invalidation →
verification checklist (six tabs render, `/api/*` round-trips, watermark advances).

### AC2/AC6 gate — `cfn-lint` joins the DoD
Add `cfn-lint infra/` (→ exit 0) to `.scrum/definition-of-done.md` "Commands (backend)" and
to CLAUDE.md's commands table, citing "second half of the 2026-07-14 DoD amendment, landed
STORY-088". Full amended gate green: pytest (incl. DynamoDB-Local), lint-imports, ruff
check, ruff format, cfn-lint + frontend (npm test/build/lint).

### Checkbox steps
- [ ] 1. Install `cfn-lint`; add to `pyproject.toml` dev extra; commit.
- [ ] 2. Author `infra/stack.yaml` to the approved resource set (iterate until
  `cfn-lint infra/` exits 0); commit.
- [ ] 3. Add `cfn-lint infra/` to `.scrum/definition-of-done.md` + CLAUDE.md commands; commit.
- [ ] 4. Author `docs/deploy-runbook.md` (all AC5 sections + the env/secret NAME table); commit.
- [ ] 5. Full amended `yt_gate.py` GREEN on a clean tree; wiki blast radius (new deploy
  article or update); commit.

---

## Gate note (applies to the orchestrator's final verification)
The amended `pytest` floor exercises the persistence layer ONLY when DynamoDB Local is
reachable (`DYNAMO_ENDPOINT_URL` set, or Docker available for `dynamo_local`); otherwise
the Dynamo-gated tests `skip` cleanly and `pytest` still exits 0 without proving
persistence. Therefore the orchestrator's independent final `yt_gate.py` run — the record
of evidence — MUST run with DynamoDB Local up (mirroring how sprint-48 provisioned a
throwaway Postgres for the DB-gated commands). A green pytest with all Dynamo tests
skipped is NOT acceptable evidence.

---

## Plan-verifier verdict
Dispatched at planning (2026-07-16; contract-sensitive on all axes — adapter/vendor wiring,
a vendor CFN template, and `external` mode). First pass: **GAPS** — every cited contract
verified clean (crucially the table-assignment table is fully confirmed against the landed
adapter tests, and the three STORY-088 CloudFront/loop-singleton mechanisms are feasible in
one template), but 6 external-mode completeness gaps found (3 HIGH would leave `pytest` red
for a literal agent). ALL FIXED pre-lock:

- GAP-1 (HIGH): `composition/seed.py` (Postgres seed, imports sqlalchemy) added to the
  deletion list; its `seed_topology` imports at `app.py:27`/`run.py:42` noted for removal.
- GAP-2 (HIGH): `test_app.py::test_app_lifespan_disposes_engine` explicitly enumerated for
  deletion (asserts the removed engine disposal; missed by the term sweep).
- GAP-3 (HIGH): the two kept Dynamo test files (`test_dynamo_observation_repository.py`,
  `test_dynamo_proposal_repository.py`) get surgical de-coupling instructions (strip
  Postgres-parity tests + top-level `psycopg`/`Postgres*`/`seed_component` imports), not
  deletion.
- GAP-4 (MEDIUM): `to_psycopg_url` removal from `run.py:48` settings import enumerated.
- GAP-5 (LOW): `create_app`'s `database_url` param → dropped; endpoint/asgi tests using
  `database_url=` → rewritten to fakes/Dynamo, not deleted.
- GAP-6 (LOW): STORY-088 Parameters gain a CloudFront origin-facing prefix-list-ID (no CFN
  intrinsic exists; `cfn-lint` won't catch a missing value).

**Status after fixes: LOCK_READY.**
