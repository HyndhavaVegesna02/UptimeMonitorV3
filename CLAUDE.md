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

### The four backend zones (dossier §4)

The backend lives under `backend/src/` as four zones. Every dependency arrow
points inward toward `core`; the core has no outgoing arrows. Boundary
violations are build failures, not review comments.

```
backend/src/
├── core/            # the constant — imports only core
│   ├── domain/      # pure data, depends on nothing
│   ├── ports/       # interfaces the core owns, in domain types
│   └── services/    # logic; calls ports, manipulates domain types
├── adapters/        # the replaceable edge — imports core, never another adapter
│   ├── inbound/     # ingest (e.g. dynatrace)
│   ├── outbound/    # publish (e.g. statuspage)
│   └── persistence/ # repositories (e.g. neon)
├── composition/     # the wiring / "main" layer — the only zone importing both sides
└── api/             # thin FastAPI HTTP surface
```

`config/` is reserved at the repo root (outside `backend/`) so that editing it
reads as a topology change rather than a code change.

### The frontend zone (dossier §17, STORY-120)

**Frontend under active greenfield rebuild — sprint-59; structure settling
across STORY-120–122.** The PO rejected two prior attempts (2026-07-19,
2026-07-21) and directed a from-scratch rebuild guided by the approved
refimg prototype; this section describes the THIRD attempt, currently just
its design-system foundation (STORY-120) — the app shell (STORY-121) and
the first real page (STORY-122) land later this sprint.

`frontend/` is a separate Vite + React + TypeScript (strict) SPA — the
operator-cockpit "internal dashboard" surface (dossier §17, "two surfaces,
not one"; the other surface is the public Statuspage). It is isolated from
the Python backend: no backend source import, no shared build step; the six
backend DoD commands never touch it and vice versa.

```
frontend/
├── src/
│   ├── styles/       # tokens.css (three-layer: primitive -> semantic -> component,
│   │                   # theme-scoped, light-only for now) + global.css
│   ├── components/    # Icon (Phosphor wrapper) + primitives: Button, Panel,
│   │                    # StatusBadge, SummaryCard, Sparkline, Loading/Error/EmptyState
│   ├── pages/          # StyleguidePage (the /styleguide design-system gallery);
│   │                    # more pages land with STORY-121/122
│   ├── lib/             # cx() classname helper
│   └── test/              # Vitest setup (jest-dom matchers)
├── index.html            # <html data-theme="light"> (no dark theme this initiative)
└── vite.config.ts         # dev proxy (/api -> http://localhost:8000) + Vitest config
```

Design reference (binding for this rebuild): the PO-approved refimg prototype
`docs/scrum/sprints/2026-07-18-ui-prototyping/prototypes/refimg-dashboard.html`
+ its derived token spec `docs/scrum/sprints/2026-07-18-ui-prototyping/
round-2-refimg-system.md` — a light-first, cool-grey-canvas, single-sky-blue-
accent system with a 7-status health palette (`up`/`degraded`/`partial`/`down`/
`maintenance`/`unknown`/`missing`) and contrast-safe text tokens (WCAG AA,
proven by a live token-contrast test). Icons are `@phosphor-icons/react`
(STORY-120), wrapped by a thin `Icon` component that requires either
`aria-hidden` or an accessible `label` at every call site. Fonts are
self-hosted Inter (`@fontsource/inter`, imported in `src/styles/global.css`)
— no runtime Google-CDN `<link>` (replaces the second attempt's self-hosted
Geist/Geist Mono). The prior `DESIGN-linear.app.md`/sprint-25/sprint-38
design lineage (Geist, the six-tab `nav/` shell, `Table`/`UptimeBar`/
`Timeline` primitives, the `api/`/`features/`/`mocks/` trees) belonged to the
now-deleted second attempt and no longer describes the tree.
`frontend/README.md` has the day-to-day quick reference.

Frontend commands (run from `frontend/`; Node 24 / npm 11):

| Task           | Command         |
| -------------- | --------------- |
| Install        | `npm install`   |
| Dev server     | `npm run dev`   |
| Build (+ tsc)  | `npm run build` |
| Test (Vitest)  | `npm test`      |
| Lint (ESLint)  | `npm run lint`  |

`npm test` (Vitest, run-once), `npm run build` (`tsc -b && vite build`), and
`npm run lint` (ESLint flat config) are the three frontend DoD gate commands,
live as of STORY-015a — see `.scrum/definition-of-done.md`. The dev server
proxies `/api/*` to `http://localhost:8000` — see "Run the app locally"
below for the recipe that gets a real backend listening there (live as of
STORY-042); CORS stays deferred to STORY-017 per the 2026-06-23 working
agreement, so no backend change was needed to wire the proxy itself.

## Stack (dossier §3)

| Surface        | Choice                                                              |
| -------------- | ------------------------------------------------------------------ |
| backend        | FastAPI on Railway — HTTP API + persistent pull-loop scheduler     |
| frontend       | React + TypeScript on Vercel — dashboard and approval UI           |
| database       | AWS DynamoDB — two tables (observations + control); DynamoDB Local for dev/CI (STORY-087) |
| observability  | Dynatrace synthetic monitors; results read from Grail via DQL      |
| demo app       | Sock Shop on Railway — the replaceable monitored app             |
| publish target | Statuspage — a fixed core target (not swappable in V3 scope)       |

## Key commands

Run from the repo root with the virtualenv active (or call the `.venv` binaries
directly on Windows: `.venv/Scripts/python.exe`, `.venv/Scripts/lint-imports.exe`).

| Task                | Command                                  |
| ------------------- | ---------------------------------------- |
| Create venv         | `python -m venv .venv`                    |
| Install (editable)  | `.venv/Scripts/python.exe -m pip install -e ".[dev]"` |
| Run tests           | `pytest`                                  |
| Verify zone imports | `python -c "import src.core, src.adapters, src.composition, src.api"` |
| Import boundary     | `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` (must exit 0; the `lint-imports` exe shim is blocked by a Windows Application Control policy since 2026-07-12) |
| Start Dynamo DB     | `docker run -d --name uptime_dynamo -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -inMemory` (host 8001 so the API can own 8000) |
| Create Dynamo tables| `python scripts/create_tables.py` (reads `DYNAMO_ENDPOINT_URL`) |
| Seed topology       | `python scripts/seed_topology.py` (reads `DYNAMO_ENDPOINT_URL`) |
| Build Docker Image  | `docker build -t uptime_monitor_v3:latest .` |
| Run API in Docker   | `docker run --rm -p 8000:8000 -e DYNAMO_ENDPOINT_URL=http://host.docker.internal:8001 uptime_monitor_v3:latest` |
| Run Loop in Docker  | `docker run --rm -e DYNAMO_ENDPOINT_URL=http://host.docker.internal:8001 uptime_monitor_v3:latest python -m src.composition.run` |
| Run live loop       | `python -m src.composition.run` (loads a repo-root `.env` at startup — STORY-043 — then runs the e2e loop) |
| Lint code           | `ruff check .` (must exit 0)               |
| Format check        | `ruff format --check .` (must exit 0)      |
| Lint CloudFormation | `cfn-lint infra/stack.yaml` (must exit 0)  |

`src` is the importable top-level package (it lives at `backend/src`, exposed via
`package-dir = {"" = "backend"}` in `pyproject.toml`).

The five DoD gate commands are `pytest`, `lint-imports`, `ruff check`, `ruff format`, and `cfn-lint`. All five are
live as of STORY-088. `lint-imports` enforces the five contracts
(core-independence, core-internal-layering, adapters-independence, api-feature-independence, src-no-tests);
`ruff check` and `ruff format` enforce the code style, import sorting, and formatting; `cfn-lint` validates the CloudFormation stack.

## Database & DynamoDB Local (dossier §3, §4, §17)

All persistence has been migrated to DynamoDB (STORY-087). The Neon Postgres database and Alembic migrations have been retired.

All DynamoDB adapters read from two tables:
- Observations table (default: `uptime-observations`)
- Control table (default: `uptime-control`)

### Live-loop secrets (STORY-016 — read by `python -m src.composition.run`)

Read from the environment via `composition/settings.py::load_live_secrets()`. The
process entrypoints (`run.py::main`, `composition/asgi.py`) load a gitignored
repo-root `.env` into the environment first, via `dotenv.load_dotenv()`
(STORY-043) — `load_settings`/`load_live_secrets` themselves only ever read
`os.environ`, never a file. An already-exported env var always wins over `.env`
(config holds the non-secret monitor id + Statuspage component id, never these
secret values):

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

### Throwaway DynamoDB for local/CI runs (no AWS needed in Sprint 0)

Under `pytest`, the session-scoped `dynamo_local` fixture (`backend/tests/conftest.py`) starts an in-memory `amazon/dynamodb-local` container if Docker is available, or reuses `DYNAMO_ENDPOINT_URL` if set, otherwise skips DynamoDB-gated tests. The table creation is automatically handled by the `clean_dynamo_tables` fixture before each test.

## Run the app locally (dossier §17, STORY-042)

The full local stack is: DynamoDB Local + the API server (uvicorn) + the live pull-loop (`python -m src.composition.run`) + the frontend dev server.

1. Start DynamoDB Local (host port 8001, leaving 8000 for the API):
   `docker run -d --name uptime_dynamo -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -inMemory`
2. Export `DYNAMO_ENDPOINT_URL="http://localhost:8001"` (or add to a repo-root `.env` file).
3. Create the DynamoDB tables:
   `python scripts/create_tables.py`
4. Start the API server on port 8000 (serves `/api/v1/*`; the boot-time lifespan seed reads `config/apps` and populates components):
   `python -m uvicorn src.composition.asgi:app --port 8000`
5. In a SECOND terminal, run the live loop to populate observations/proposals/publications — needs the Dynatrace/Statuspage secrets, either exported or in the same repo-root `.env` (with `DYNAMO_ENDPOINT_URL` also configured):
   `python -m src.composition.run`
6. In a THIRD terminal:
   `cd frontend && npm run dev`

## Tooling inventory

| Tool              | Version / note                | Purpose                                   |
| ----------------- | ----------------------------- | ----------------------------------------- |
| Python            | 3.13.9 (miniconda)            | runtime                                   |
| pip               | 25.2                          | package management                        |
| pytest            | test runner (DoD gate)        | `pytest` must exit 0                       |
| import-linter     | `lint-imports` (live, STORY-002)| enforces zone dependency boundaries (DoD)|
| Docker            | 28.5.2                        | throwaway DynamoDB local run              |
| boto3             | runtime dependency             | AWS SDK for DynamoDB operations           |
| `scripts/create_tables.py` | live (STORY-082)       | table creation helper                     |
| ruff              | live (STORY-033); `ruff check` + `ruff format` (DoD) | code style, sorting, and formatting |
| uvicorn[standard] | live (STORY-042); dev dependency | local ASGI dev server — `uvicorn src.composition.asgi:app` |
| httpx             | runtime dependency             | HTTP library for query and statuspage executors |
| python-dotenv     | live (STORY-043); runtime dependency | `.env` loading at the two process entrypoints (`run.py::main`, `composition/asgi.py`) |
| git               | configured                    | version control                           |
| cfn-lint          | live (STORY-088); dev dependency | CloudFormation validation tool (DoD)      |

No `psql` client or SQL databases are used. Dynatrace/Statuspage credentials and DynamoDB settings are read from environment variables, exported directly or loaded from a gitignored repo-root `.env` (STORY-043) for the live loop.

## Deployed topology (STORY-089, live since 2026-07-17)

The system runs live in AWS **us-east-1**, account `065317679010`, as CloudFormation stack
`uptime-monitor` (from `infra/stack.yaml`; deploy procedure: `docs/deploy-runbook.md`).
Full live-verified detail: `docs/scrum/wiki/deployment-topology.md`.

| Piece          | Live value                                                              |
| -------------- | ----------------------------------------------------------------------- |
| Public URL     | `https://d3ukiib1iqmbxb.cloudfront.net` (SPA + same-origin `/api/*`)    |
| ECS cluster    | `uptime-monitor-cluster` — services `uptime-monitor-api` (behind the ALB) + `uptime-monitor-loop` (singleton) |
| Image          | `065317679010.dkr.ecr.us-east-1.amazonaws.com/uptime-monitor-repo:latest` |
| Tables         | `uptime-monitor-observations`, `uptime-monitor-control` (DeletionPolicy Retain) |
| Secrets (names)| `uptime-monitor-dynatrace-secrets` (`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`); `uptime-monitor-statuspage-secrets` (`STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`) — values ONLY in Secrets Manager |
| Plain env vars | `AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE` (injected by task defs) |
| Logs           | `/ecs/uptime-monitor-api`, `/ecs/uptime-monitor-loop` (CloudWatch, 14 days) |

Quick verify: `curl https://d3ukiib1iqmbxb.cloudfront.net/api/v1/health` → 200;
`aws ecs describe-services --cluster uptime-monitor-cluster --services uptime-monitor-api uptime-monitor-loop`
→ both 1/1 running. Company account rules (region lock us-east-1, `c7n-keep=true` tagging
against the 22:00 IST reaper): see `docs/deploy-runbook.md` Prerequisites.
