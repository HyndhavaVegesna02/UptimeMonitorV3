# Uptime Monitor V3

This project follows the YourTeam skill. At session start, read `.scrum/sprint-current.yaml` and resume from board state. Honor `.scrum/working-agreements.md`.

## Project overview

A ground-up redesign of an uptime/status monitoring system. It consumes real
multi-location synthetic monitor results from Dynatrace and publishes to a live
Statuspage, keeping V2's hard-won business logic (anti-flap, human-approved
degradations, availability-vs-status separation) while replacing its structure
with a clean hexagonal architecture. The spec / source of truth is
`uptime-monitor-v3-design.html` — build to it and the story AC, never to chat
history.

Superseded decisions (Railway/Vercel, Neon Postgres, the rejected UI attempts,
`sample_mode`, design lineage): `docs/project-history.md`. Read it only when a
decision looks wrong and you are about to change it.

### Two things to know before you touch anything

1. **No live vendor data since 2026-07-28.** The Dynatrace trial expired, so no
   observations arrive and nothing is verifiable against real vendor traffic. The
   PO-approved substitute is the local demo engine below. `sample_mode` still
   exists but is inert for the same reason; its removal is STORY-155.
2. **No vendor FAILURE code has ever been observed — the two we map are ASSUMPTIONS.**
   `map_synthetic_status` (`adapters/inbound/dynatrace/health_mapping.py`) resolves in
   three steps: the healthy OR-rule (`code == "0"` **or** `message == "HEALTHY"` →
   `Health.UP`); then an **exact** `(code, message)` tuple lookup in
   `PROVISIONAL_STATUS_MAPPING` — `("1","UNHEALTHY") → DOWN`, `("2","DEGRADED") →
   DEGRADED` — logging a WARNING naming the code and its unverified status; then a raise
   (`UnknownVendorStatusError`) naming the real code, so a genuine vendor failure value
   still surfaces to be read and mapped. Those two pairs are **provisional and unverified**
   (STORY-177); STORY-154 replaces that one constant's contents when a tenant exists. They
   live in exactly one place — `tools/` derives them, never redeclares them.
   A bad row costs only itself: it is quarantined via `RejectedObservationRepository`,
   the rest of the batch ingests, and the watermark advances (STORY-190).
   So "the failure path is tested" is true in a **specific, limited sense**: tested
   against an ASSUMED code, through the real unmodified ingest path, in a real loop run
   (STORY-191) — never against anything Dynatrace has confirmed. Say it that way, not flatly.

### Repo layout

```
backend/src/        # the four zones (dossier §4) — see below
config/             # per-app topology YAML, deliberately OUTSIDE backend/ so
                    #   editing it reads as a topology change, not a code change
frontend/           # the operator-cockpit SPA (separate toolchain)
tools/              # dev-only, never in the production image
scripts/            # create_tables.py, seed_topology.py, dynamo_local.py
infra/stack.yaml    # the CloudFormation stack
```

### The four backend zones (dossier §4)

Every dependency arrow points inward toward `core`; the core has no outgoing
arrows. Boundary violations are build failures, not review comments — see the
`lint-imports` gate below.

```
backend/src/
├── core/            # the constant — imports only core
│   ├── domain/      # pure data, depends on nothing
│   ├── ports/       # interfaces the core owns, in domain types
│   └── services/    # logic; calls ports, manipulates domain types
├── adapters/        # the replaceable edge — imports core, never another adapter
│   ├── inbound/     # ingest (dynatrace)
│   ├── outbound/    # publish (statuspage)
│   └── persistence/ # repositories (dynamo_*, one per port)
├── composition/     # the wiring / "main" layer — the only zone importing both sides
└── api/             # thin FastAPI HTTP surface (five-file features under api/v1/)
```

### The frontend zone (dossier §17)

`frontend/` is a separate Vite + React + TypeScript (strict) SPA — the
operator-cockpit "internal dashboard" surface (dossier §17, "two surfaces, not
one"; the other is the public Statuspage). It is isolated from the Python backend:
no backend source import, no shared build step; the five backend DoD commands never
touch it and vice versa. Six-tab IA with one source of truth for sidebar AND routing
(`src/nav/tabs.ts`). Fonts are self-hosted Geist + Geist Mono — no runtime
Google-CDN `<link>`.

Structure and conventions: `frontend/README.md`; full detail
`docs/scrum/wiki/frontend-zone.md`.

**Design reference:** the PO-built UI at `C:\Hyn\new ui\ops-pulse-react` — *visual*
only, no data layer. The in-repo capture is authoritative:
`docs/scrum/sprints/2026-07-28-sprint-62/` holds `newui-01..08-*.png` plus
`ui-backend-gap-analysis.md`, mapping every screen to `api/v1` with `file:line`
citations. A frontend sprint ports the design system from it and ends with a **PO
look-and-feel checkpoint on the styleguide + shell, before any pages are built on
the language** — three previous attempts were rejected for skipping that
(`docs/project-history.md`).

Frontend commands (run from `frontend/`; Node 24 / npm 11):

| Task           | Command         |
| -------------- | --------------- |
| Install        | `npm install`   |
| Dev server     | `npm run dev`   |
| Build (+ tsc)  | `npm run build` |
| Test (Vitest)  | `npm test`      |
| Lint (ESLint)  | `npm run lint`  |

The dev server proxies `/api/*` to `http://localhost:8000`. **No CORS middleware
exists and none is needed:** dev goes through that proxy, production is same-origin
behind CloudFront. `api/v1/_shared/middleware.py` is an empty seam.

### The Grail demo engine (`tools/demo_engine/`)

A local HTTP server speaking the Dynatrace Grail `query:execute` wire protocol
faithfully enough that the **real, unmodified** `make_grail_executor` can talk to it
— the stand-in for the expired trial. It lives under `tools/`, deliberately outside
`backend/src/`: it can never enter the production image, it may import `src.*`, and
nothing under `backend/src/` ever imports it.

It emits **`HEALTHY` rows and absence, nothing else**, so any failure code here is an
explicitly-labelled assumption (`tools/demo_engine/assumed_failure_codes.py`), not a
contract. The demo fleet is `config/demo/` — **never `config/apps/`**.

Scenario player, fleet coverage, the proven loop run (STORY-182) and the full wire
contract: `docs/scrum/wiki/demo-engine.md`.

> ⚠ **The publish guard is config-only, and needs `CONFIG_DIR` set on BOTH processes
> — not just the loop.** `config/demo/` declares no `statuspage_component_id`, so
> `Config.statuspage_mapping()` is `{}` and `build_publisher` falls through to a
> `LoggingPublisher` **even with real Statuspage credentials present** (the repo-root
> `.env` supplies them from any launch directory — `load_dotenv()` walks up from the
> source file, not CWD). Two composition roots build a live publisher from those
> credentials and BOTH must point at `config/demo/`:
> - the loop, via `composition/run.py::main` → `build_live_loop`
> - the API's **approve trigger**, via `composition/app.py::create_app`
>
> Both read `CONFIG_DIR`, defaulting to `config/apps` — which declares a REAL
> `statuspage_component_id`. Setting it on only one leaves the other resolving the
> real page. Demo component ids are kept **disjoint** from `config/apps`'s, because
> `StatuspagePublisher` keys on the canonical component id and a collision would PATCH
> the live page even with the guard in place.

## Stack (dossier §3)

| Surface        | Choice                                                                |
| -------------- | --------------------------------------------------------------------- |
| backend        | FastAPI on **AWS ECS Fargate** — HTTP API service + singleton pull-loop service |
| frontend       | React + TypeScript, static build served by **CloudFront** (same origin as `/api/*`) |
| database       | **AWS DynamoDB** — two tables (observations + control); DynamoDB Local for dev/CI |
| observability  | Dynatrace synthetic monitors; results read from Grail via DQL          |
| monitored app  | Whatever `config/apps/*.yaml` declares — today one HTTP check (`httpcheck.yaml`) |
| publish target | Statuspage — a fixed core target (not swappable in V3 scope)           |

> The backend/frontend rows above are the **target architecture** (dossier §3) that
> `infra/stack.yaml` builds to, not a claim that AWS is currently running it — the concrete
> deployment built to this design was **decommissioned on 2026-08-13** (see "Deployed
> topology" below). There is currently no live AWS environment; dev/CI runs entirely against
> DynamoDB Local and the Vite dev server.

## Key commands

Run from the repo root with the virtualenv active (or call `.venv/Scripts/python.exe`
directly on Windows). **Three console-script shims are blocked by this machine's
Windows Device Guard / Application Control policy and must be invoked via their module
or entry-point form instead** — the check performed is identical, only the entry point
differs: `lint-imports.exe` (blocked 2026-07-12), `pytest.exe` + `cfn-lint.exe`
(blocked 2026-07-31; see STORY-210). `cfn-lint` needs its entry point
(`cfnlint.runner:main`) rather than `-m`, because the package has no `__main__`.
`ruff check .` / `ruff format --check .` below are ALSO module-form (`python -m ruff
...`), but `ruff.exe` is NOT one of the three blocked shims — that move is preventive
(STORY-210), taken because the policy has already widened twice unannounced.

| Task                | Command                                  |
| ------------------- | ---------------------------------------- |
| Create venv         | `python -m venv .venv`                    |
| Install (editable)  | `.venv/Scripts/python.exe -m pip install -e ".[dev]"` |
| Run tests           | `python -m pytest`                        |
| Verify zone imports | `python -c "import src.core, src.adapters, src.composition, src.api"` |
| Import boundary     | `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` |
| Lint code           | `python -m ruff check .`                  |
| Format check        | `python -m ruff format --check .`         |
| Lint CloudFormation | `python -c "from cfnlint.runner import main; main()" infra/stack.yaml` |
| Start DynamoDB Local| `docker run -d --name uptime_dynamo -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -inMemory` (host 8001 so the API can own 8000) |
| Create tables       | `python scripts/create_tables.py` (reads `DYNAMO_ENDPOINT_URL`) |
| Seed topology       | `python scripts/seed_topology.py` (reads `DYNAMO_ENDPOINT_URL`) |
| Build Docker image  | `docker build -t uptime_monitor_v3:latest .` |
| Run API in Docker   | `docker run --rm -p 8000:8000 -e DYNAMO_ENDPOINT_URL=http://host.docker.internal:8001 uptime_monitor_v3:latest` |
| Run loop in Docker  | `docker run --rm -e DYNAMO_ENDPOINT_URL=http://host.docker.internal:8001 uptime_monitor_v3:latest python -m src.composition.run` |
| Run live loop       | `python -m src.composition.run` (loads a repo-root `.env` first, then runs the e2e loop) |

`src` is the importable top-level package (it lives at `backend/src`, exposed via
`package-dir = {"" = "backend"}` in `pyproject.toml`). **That editable install is a
plain absolute `sys.path` entry**, so `src.*` resolves to the MAIN tree from inside
any git worktree — force `PYTHONPATH=<worktree>/backend` when a check must run the
worktree's code (`tools/import_provenance.py::assert_import_root`).

### The DoD gate — 8 commands, all must exit 0

`.scrum/definition-of-done.md` is authoritative; the runner is
`python .claude/skills/yourteam/scripts/yt_gate.py`.

- **Backend (5):** `python -m pytest`, the import-boundary `python -c` above,
  `python -m ruff check .`, `python -m ruff format --check .`, and cfn-lint via
  `python -c "from cfnlint.runner import main; main()" infra/stack.yaml`
- **Frontend (3, from `frontend/`):** `npm test`, `npm run build`, `npm run lint`

`lint-imports` enforces nine zone contracts (STORY-206 added `inbound-adapters-dont-persist`,
ZR-1's guard); `ruff` covers style, import sorting and formatting; `cfn-lint` validates the
CloudFormation stack.

## Database & DynamoDB Local (dossier §3, §4, §17)

All persistence is DynamoDB — two tables, one repository module per port under
`adapters/persistence/`: observations (default `uptime-observations`) and control
(default `uptime-control`).

### Live-loop secrets (read by `python -m src.composition.run`)

Read from the environment via `composition/settings.py::load_live_secrets()`. The two
process entrypoints (`run.py::main`, `composition/asgi.py`) load a gitignored
repo-root `.env` into the environment first via `dotenv.load_dotenv()` —
`load_settings`/`load_live_secrets` themselves only ever read `os.environ`, never a
file. An already-exported env var always wins over `.env`. Config holds the non-secret
monitor id + Statuspage component id, never these secret values:

| Env var                     | Used for                                                          |
| --------------------------- | ---------------------------------------------------------------- |
| `AWS_REGION`                | AWS Region (default: `us-east-1`)                                |
| `DYNAMO_OBSERVATIONS_TABLE` | Observations table name                                          |
| `DYNAMO_CONTROL_TABLE`      | Control table name                                               |
| `DYNAMO_ENDPOINT_URL`       | Local DynamoDB endpoint URL (e.g. `http://localhost:8001`)       |
| `DYNATRACE_ENV_URL`         | Dynatrace tenant base URL (Grail DQL execute endpoint)           |
| `DYNATRACE_API_TOKEN`       | Dynatrace platform token (scopes `storage:buckets:read storage:events:read`) |
| `STATUSPAGE_PAGE_ID`        | Statuspage page id                                               |
| `STATUSPAGE_API_KEY`        | Statuspage API token (→ `Settings.statuspage_api_token`)         |
| `REQUIRE_DYNAMO`            | Set non-empty in CI/gate: makes `dynamo_local` FAIL instead of skip |

⚠ `decide` publishes **recoveries with no human gate**
(`core/services/decide.py`), so any loop run wired to the real publisher can post to
the LIVE public Statuspage. Guard demo/local loop runs with the config-only publish
guard above *and* `CONFIG_DIR` on the API process, which is a separate process reading
its own config.

### Throwaway DynamoDB for local/CI runs

Under `pytest`, the session-scoped `dynamo_local` fixture (`backend/tests/conftest.py`)
starts an in-memory `amazon/dynamodb-local` container if Docker is available, reuses
`DYNAMO_ENDPOINT_URL` if set, otherwise skips DynamoDB-gated tests — unless
`REQUIRE_DYNAMO` is set, which makes it FAIL instead. **A nonzero skip count is an
incomplete gate, not a pass** (a green `pytest` once hid the entire 53-test persistence
floor because Docker was down). Known defect: the ephemeral host port the fixture picks
is mapped by Docker but not always routable on Windows — set `DYNAMO_ENDPOINT_URL` to a
fixed-port container to work around it (STORY-179).

## Run the app locally

Full local stack: DynamoDB Local + the API server (uvicorn) + the live pull-loop + the
frontend dev server.

1. Start DynamoDB Local — the `docker run` in Key commands (host port 8001, leaving
   8000 for the API).
2. Export `DYNAMO_ENDPOINT_URL="http://localhost:8001"` (or put it in a repo-root `.env`).
3. `python scripts/create_tables.py`
4. Start the API on port 8000 (serves `/api/v1/*`; the boot-time lifespan seed reads
   `config/apps` and populates components):
   `python -m uvicorn src.composition.asgi:app --port 8000`
5. SECOND terminal — the live loop (needs the Dynatrace/Statuspage secrets, exported or
   in the same `.env`; read the publish warning above first):
   `python -m src.composition.run`
6. THIRD terminal: `cd frontend && npm run dev`

## Tooling

Python 3.13 (repo `.venv`), ruff, cfn-lint, import-linter (invoked as a module, not the
exe), pytest, Docker (DynamoDB Local), Node 24 / npm 11, uvicorn (dev).
`pyproject.toml` is the source of truth for versions — do not duplicate them here. No
`psql` client and no SQL database is used.

`[tool.ruff]` sets `exclude = [".agents", ".venv", "frontend"]`, so `ruff check .` /
`ruff format --check .` do **not** scan the frontend (it has its own ESLint gate) — but they
DO scan `.claude/`, which is not excluded.

**Line endings are LF in the repo**, via `.gitattributes` (`* text=auto eol=lf` plus `binary`
rules for `*.png/jpg/jpeg/gif/ico/pdf/woff/woff2`; STORY-018). The index blobs are already LF,
so `git add --renormalize .` stages nothing: the CRLF a Windows checkout shows in the *working
tree* comes from a global `core.autocrlf=true` at checkout time, not from repo content. The
`CRLF will be replaced by LF` warning on `git add` is that conversion, not a problem to fix.

## Deployed topology (STORY-089) — DECOMMISSIONED 2026-08-13

**The AWS stack was brought down by PO decision on 2026-08-13** (`aws cloudformation
delete-stack --stack-name uptime-monitor`, or equivalent). This section is now **history** —
what was deployed, and its last known status before the decommission — not something to
re-verify against a live URL.

**The teardown was VERIFIED COMPLETE on 2026-08-13 — nothing survived, and there is nothing to
clean up before a redeploy.** Checked against the live account (`sts get-caller-identity` →
`065317679010`):

| Checked | Result |
| --- | --- |
| `cloudformation describe-stacks --stack-name uptime-monitor` | `ValidationError: does not exist` |
| `dynamodb list-tables` | neither `uptime-monitor-observations` nor `uptime-monitor-control` present |
| `s3 ls` | no `uptime-monitor-frontend-065317679010` bucket |
| `ecs list-clusters` | no `uptime-monitor-cluster` |
| DNS for the CloudFront domain | does not resolve (a *disabled* distribution still would) |

This was worth checking rather than assuming, because **`infra/stack.yaml` sets
`DeletionPolicy: Retain` on `ObservationsTable`, `ControlTable` and `FrontendBucket`** — so a
`delete-stack` leaves those three behind *by design*, and `docs/scrum/wiki/deployment-topology.md`
records that exactly this kind of Retain leftover has blocked a fresh `create-stack` by name
before. They were cleared anyway (by hand or by the account reaper), so that hazard did not land
this time.

⚠ **The `Retain` policy is still in the template**, so a future deploy-then-teardown cycle
recreates the hazard. Decide whether `Retain` is actually wanted on those three resources before
the stack is ever re-created.

**What was deployed (historical, AWS us-east-1, account `065317679010`):**

- **Public URL (past):** `https://d3ukiib1iqmbxb.cloudfront.net` (SPA + same-origin `/api/*`)
- **ECS cluster (past):** `uptime-monitor-cluster` — services `uptime-monitor-api` (behind the
  ALB) + `uptime-monitor-loop` (singleton)
- **Secrets (past):** lived ONLY in Secrets Manager: `uptime-monitor-dynatrace-secrets`,
  `uptime-monitor-statuspage-secrets`. Plain env vars (`AWS_REGION`, both table names) were
  injected by the task definitions.
- **Status before decommission:** last verified healthy 2026-07-17; a 2026-07-29 re-check got a
  503 from `/api/v1/health` with expired AWS credentials, so the cause of that 503 was never
  confirmed (likeliest: the 22:00 IST reaper stopping ECS tasks that lost their
  `c7n-keep=true` tag) — that particular question is moot now that the stack was brought down,
  but it means the environment's *last confirmed-good* state is 2026-07-17, not 2026-07-29.

Full detail of the deployed instance (now historical): `docs/scrum/wiki/deployment-topology.md`.
The CloudFormation template + Dockerfile that built it, and the redeploy procedure:
`docs/deploy-runbook.md` and `docs/scrum/wiki/deployment-and-infra.md` (also a tombstone as of
this decommission, STORY-222). A redeploy decision has not been made; STORY-090 (CI/CD) stays
archived on the same "no live stack" fact.

Company account rules that applied while live (region lock us-east-1, `c7n-keep=true` tagging
against the reaper): `docs/deploy-runbook.md` Prerequisites — still correct for any future
redeploy.
