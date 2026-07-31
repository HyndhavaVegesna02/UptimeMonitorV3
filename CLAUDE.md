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

### Two things to know before you touch anything

1. **No live vendor data since 2026-07-28.** The Dynatrace trial expired, so no
   observations arrive and nothing is verifiable against real vendor traffic. The
   PO-approved substitute is the local demo engine below. `sample_mode` (which
   flips already-normalized rows) still exists but is inert for the same reason;
   its removal is STORY-155.
2. **No vendor FAILURE code has ever been observed — the two we map are ASSUMPTIONS.**
   `map_synthetic_status` (`adapters/inbound/dynatrace/health_mapping.py`) resolves in
   three steps: the healthy OR-rule (`code == "0"` **or** `message == "HEALTHY"` →
   `Health.UP`) first and unchanged; then an **exact** `(code, message)` tuple lookup in
   `PROVISIONAL_STATUS_MAPPING` — `("1","UNHEALTHY") → DOWN`, `("2","DEGRADED") →
   DEGRADED` — logging a WARNING naming the code and its unverified status; then a raise
   (`UnknownVendorStatusError`) naming the real code, so a genuine vendor failure value
   still surfaces to be read and mapped. Those two pairs are **provisional and unverified**
   (STORY-177); the trial expired before a real code could be captured, and STORY-154
   replaces the contents of that one constant when a tenant exists. They live in exactly
   one place — `tools/` derives them, never redeclares them.
   So "the failure path is tested" is now true in a **specific, limited sense**: tested
   against an ASSUMED code, through the real unmodified ingest path, in a real loop run
   (STORY-191) — never against anything Dynatrace has confirmed. Say it that way, not flatly.
   **Superseded, so it is not re-litigated:** this section used to say `map_synthetic_status`
   RAISES on everything else, that `dispatch.py` then discards the whole batch, and that
   `DOWN`/`DEGRADED` cannot reach the pipeline at all. All three were true until sprint 65
   and are now false — STORY-190 also made a bad row cost only itself (it is quarantined via
   `RejectedObservationRepository`; the rest of the batch ingests and the watermark advances,
   where previously one unmappable row stalled that signal permanently).

### Repo layout

```
backend/src/        # the four zones (dossier §4) — see below
config/             # per-app topology YAML, deliberately OUTSIDE backend/ so
                    #   editing it reads as a topology change, not a code change
frontend/           # the operator-cockpit SPA (separate toolchain)
tools/              # dev-only, never in the production image
  demo_engine/      #   the Grail wire-protocol stand-in (STORY-148)
  ui-sweep/         #   Playwright UI sweep harness (STORY-095)
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
one"; the other surface is the public Statuspage). It is isolated from the Python
backend: no backend source import, no shared build step; the five backend DoD
commands never touch it and vice versa.

```
frontend/
├── src/
│   ├── AppShell.tsx    # shell + routing, driven by nav/tabs.ts
│   ├── styles/         # tokens.css (theme-scoped custom properties) + global.css
│   ├── theme/          # theme resolution (system pref + localStorage), ThemeProvider/useTheme
│   ├── components/     # Button, StatusBadge, Panel, Loading/Error/EmptyState, Icon,
│   │                   #   Table, UptimeBar, SummaryCard, Timeline
│   ├── nav/            # Sidebar (dark inset) + TopBar + SampleModeBanner + tabs.ts —
│   │                   #   the six-tab IA, one source of truth for sidebar AND routing
│   ├── pages/          # six real pages, one per tab, + NotFoundPage
│   ├── features/       # per-tab logic, one dir per tab (+ shell/)
│   ├── api/            # client.ts + DTO types mirroring backend/src/api/v1/*/models.py
│   ├── lib/            # cx.ts, useFetch.ts
│   ├── mocks/          # MSW handlers + node server (the only mocked I/O edge in tests)
│   └── test/           # Vitest setup (jest-dom matchers, MSW server lifecycle)
├── index.html          # pre-paint inline theme-resolution script (no flash)
└── vite.config.ts      # dev proxy (/api -> http://localhost:8000) + Vitest config
```

**Design reference (current):** the PO-built UI at `C:\Hyn\new ui\ops-pulse-react`
— a *visual* reference only (no data layer: 0 `.map()` calls across its six pages).
The in-repo capture is authoritative: `docs/scrum/sprints/2026-07-28-sprint-62/`
holds `newui-01..08-*.png` (six routes at 1440 light+dark and 390) plus
`ui-backend-gap-analysis.md`, which maps every screen to the `api/v1` surface with
`file:line` citations. The frontend sprint ports the design system from it (tokens,
glass surfaces, dark inset sidebar) and ends with a **PO look-and-feel checkpoint on
the styleguide + shell, before any pages are built on the language**.

Fonts are self-hosted Geist + Geist Mono (`@fontsource/geist` +
`@fontsource/geist-mono`, imported in `src/styles/global.css`) — no runtime
Google-CDN `<link>`. `frontend/README.md` has the day-to-day quick reference.

Frontend commands (run from `frontend/`; Node 24 / npm 11):

| Task           | Command         |
| -------------- | --------------- |
| Install        | `npm install`   |
| Dev server     | `npm run dev`   |
| Build (+ tsc)  | `npm run build` |
| Test (Vitest)  | `npm test`      |
| Lint (ESLint)  | `npm run lint`  |

The dev server proxies `/api/*` to `http://localhost:8000` — see "Run the app
locally" for the recipe that gets a real backend listening there. **No CORS
middleware exists and none is needed:** dev goes through that proxy, production is
same-origin behind CloudFront. `api/v1/_shared/middleware.py` is an empty seam.

### The Grail demo engine (`tools/demo_engine/`, STORY-148)

A local HTTP server that speaks the Dynatrace Grail `query:execute` wire protocol
faithfully enough that the **real, unmodified** `make_grail_executor` can talk to
it — the stand-in for the expired trial. It lives under `tools/`, deliberately
outside `backend/src/`: it can never enter the production image, it may import
`src.*`, and nothing under `backend/src/` ever imports it. Importable from tests
via a `sys.path` insertion in the one shared `backend/tests/conftest.py`; tests
live in `backend/tests/demo_engine/`.

It emits **`HEALTHY` rows and absence, nothing else** (see "Two things to know"
above), so any failure code here is an explicitly-labelled assumption
(`tools/demo_engine/assumed_failure_codes.py`), not a contract. Full detail:
`docs/scrum/wiki/demo-engine.md`.

**Part 2a (STORY-176): a scenario player, a demo fleet, and a publish guard —
the run itself is still not wired up (that's STORY-182).** `tools/demo_engine/
scenario.py` expands a scenario YAML (per-signal, per-cycle, per-location `UP`
outcomes — absence is the only other outcome this `UP`-and-absence-only engine
can express) into Grail-shaped rows, **past-anchored** to `end_time` (the
scenario's last cycle lands there; earlier cycles land successively further
back at the monitor's own `interval_seconds`) so the whole declared ladder is
inside `orchestrate.py`'s rolling window on the very first query, and no row
is ever timestamped in the future **provided `interval_seconds` is positive —
`load_scenario_file` now rejects a non-positive value at load time
(`InvalidScenarioError`), since that is the one input that would otherwise
make expansion land in the future**. `config/demo/` is a fictional fleet (13
components, 41 signals, 4 declared locations) authored in STORY-146's nested
shape — **never `config/apps/`**; `config/demo/scenarios/` covers the cases
reachable without a failure-code mapping (a clean fleet, a dark location, a
dark monitor, staggered intervals, a late-returning monitor).

**The publish guard is config-only, and needs `CONFIG_DIR` set on BOTH
processes it could reach — not just the loop.** `config/demo/` declares
**no** `statuspage_component_id` on any component, so `Config.
statuspage_mapping()` is `{}` and `build_publisher` (`publish_helper.py:211`)
falls through to a `LoggingPublisher` delegate **even with real Statuspage
credentials present** (the repo-root `.env` supplies them from any launch
directory — `run.py:178`'s `load_dotenv()` walks up from the source file, not
CWD). Two composition roots build a live publisher from those credentials and
BOTH must point at `config/demo/`, or neither does:
- the loop, via `composition/run.py::main` -> `build_live_loop` (reads
  `settings.config_dir`, i.e. `CONFIG_DIR`, defaulting to `config/apps`,
  `settings.py:32`);
- the API's **approve trigger**, via `composition/app.py::create_app` (no
  `config_dir` argument in the documented recipe below -> `CONFIG_DIR`
  governs it exactly the same way).

Setting `CONFIG_DIR` on only one of the two still leaves the OTHER process
resolving `config/apps` by default — which declares a real
`statuspage_component_id` (`config/apps/httpcheck.yaml:8`). Demo component ids
are also kept **disjoint** from `config/apps`'s (`StatuspagePublisher` keys on
the canonical component id, `adapters/outbound/statuspage/__init__.py:41-46`,
so a collision would PATCH the real page even with the guard above in place).

**The loop HAS now been run against the demo fleet (STORY-182, sprint 64) —
proven, not merely guarded.** `tools/demo_loop_gate/harness.py::run_positive_side`
drives the real, unmodified `python -m src.composition.run` as an OS
subprocess against an embedded local demo-engine instance, with `CONFIG_DIR`
set to `config/demo` on **both** it and a real `uvicorn` API subprocess, fresh
throwaway DynamoDB tables (`tools/demo_loop_gate/env_matrix.py::
fresh_table_names`), and deliberately fake Dynatrace/Statuspage credentials on
**both** subprocesses' env — a defence-in-depth on top of the actual guard.
The API process is genuinely credential-bearing: `composition/app.py:169-183`
calls `load_statuspage_secrets()` and wires both Statuspage vars into
`build_publisher()` for the approve trigger, so if the harness omitted the
fakes there, that subprocess's own `load_dotenv()` (`composition/asgi.py`)
would supply the REAL repo-root `.env` values instead. The real guard is
`config/demo`'s empty `statuspage_mapping()` (verified independently, with no
network call, by `tools/demo_loop_gate/guard_reality_gate.py`), never the
absence of credentials on either process. The five checked-in
`config/demo/scenarios/*.yaml` cover only 6 of the fleet's 41 signals by
design (STORY-176 AC5's specific cases); STORY-182 closed that gap with a
**fleet-wide coverage artifact built in code**
(`tools/demo_loop_gate/fleet_coverage.py::build_fleet_row_store`), one
`SignalScenario` per configured signal, 5 cycles across all 4 declared
locations — verified to make `check_vendor_id_health` (`composition/
vendor_health.py`) report zero dead ids and every signal ingest at least
one observation from each of its 4 locations. This is a **repeatable proof
harness**, not a standing/scheduled service: nothing in this repo starts the
loop automatically, and every run still needs the guard above (`CONFIG_DIR`
on both processes) — `decide` still publishes recoveries with no human gate
(`core/services/decide.py:122-126` decides, `:171-172` publishes), so the
guard is the reason a proof run never reached the real Statuspage (verified
independently, with no network call, by `tools/demo_loop_gate/
guard_reality_gate.py`).

## Stack (dossier §3)

| Surface        | Choice                                                                |
| -------------- | --------------------------------------------------------------------- |
| backend        | FastAPI on **AWS ECS Fargate** — HTTP API service + singleton pull-loop service |
| frontend       | React + TypeScript, static build served by **CloudFront** (same origin as `/api/*`) |
| database       | **AWS DynamoDB** — two tables (observations + control); DynamoDB Local for dev/CI |
| observability  | Dynatrace synthetic monitors; results read from Grail via DQL          |
| monitored app  | Whatever `config/apps/*.yaml` declares — today one HTTP check (`httpcheck.yaml`) |
| publish target | Statuspage — a fixed core target (not swappable in V3 scope)           |

## Key commands

Run from the repo root with the virtualenv active (or call `.venv/Scripts/python.exe`
directly on Windows). **Three console-script shims are blocked by this machine's
Windows Device Guard / Application Control policy and must be invoked via their module
or entry-point form instead** — the check performed is identical in every case, only the
entry point differs:
`lint-imports.exe` (blocked 2026-07-12), and `pytest.exe` + `cfn-lint.exe` (blocked
2026-07-31, mid-sprint-66 — green at 11:16 UTC, blocked at 16:33 UTC the same day with
no code change in between; see STORY-210). `cfn-lint` needs its entry point
(`cfnlint.runner:main`) rather than `-m`, because the package has no `__main__`.

| Task                | Command                                  |
| ------------------- | ---------------------------------------- |
| Create venv         | `python -m venv .venv`                    |
| Install (editable)  | `.venv/Scripts/python.exe -m pip install -e ".[dev]"` |
| Run tests           | `python -m pytest`                        |
| Verify zone imports | `python -c "import src.core, src.adapters, src.composition, src.api"` |
| Import boundary     | `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"` |
| Lint code           | `ruff check .`                            |
| Format check        | `ruff format --check .`                   |
| Lint CloudFormation | `python -c "from cfnlint.runner import main; main()" infra/stack.yaml` |
| Start DynamoDB Local| `docker run -d --name uptime_dynamo -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -inMemory` (host 8001 so the API can own 8000) |
| Create tables       | `python scripts/create_tables.py` (reads `DYNAMO_ENDPOINT_URL`) |
| Seed topology       | `python scripts/seed_topology.py` (reads `DYNAMO_ENDPOINT_URL`) |
| Build Docker image  | `docker build -t uptime_monitor_v3:latest .` |
| Run API in Docker   | `docker run --rm -p 8000:8000 -e DYNAMO_ENDPOINT_URL=http://host.docker.internal:8001 uptime_monitor_v3:latest` |
| Run loop in Docker  | `docker run --rm -e DYNAMO_ENDPOINT_URL=http://host.docker.internal:8001 uptime_monitor_v3:latest python -m src.composition.run` |
| Run live loop       | `python -m src.composition.run` (loads a repo-root `.env` first, then runs the e2e loop) |

`src` is the importable top-level package (it lives at `backend/src`, exposed via
`package-dir = {"" = "backend"}` in `pyproject.toml`).

### The DoD gate — 8 commands, all must exit 0

`.scrum/definition-of-done.md` is authoritative; the runner is
`python .claude/skills/yourteam/scripts/yt_gate.py`.

- **Backend (5):** `python -m pytest`, the import-boundary `python -c` above,
  `ruff check .`, `ruff format --check .`, and cfn-lint via
  `python -c "from cfnlint.runner import main; main()" infra/stack.yaml`
- **Frontend (3, from `frontend/`):** `npm test`, `npm run build`, `npm run lint`

`lint-imports` enforces **eight** contracts: core-independence,
core-internal-layering, adapters-independence, api-feature-independence,
api-outward-independence, adapters-edge-only, api-shared-no-feature-imports,
src-no-tests. `ruff` covers style, import sorting and formatting; `cfn-lint`
validates the CloudFormation stack.

## Database & DynamoDB Local (dossier §3, §4, §17)

All persistence is DynamoDB — two tables, one repository module per port under
`adapters/persistence/`:

- Observations table (default: `uptime-observations`)
- Control table (default: `uptime-control`)

### Live-loop secrets (read by `python -m src.composition.run`)

Read from the environment via `composition/settings.py::load_live_secrets()`. The
two process entrypoints (`run.py::main`, `composition/asgi.py`) load a gitignored
repo-root `.env` into the environment first via `dotenv.load_dotenv()` —
`load_settings`/`load_live_secrets` themselves only ever read `os.environ`, never a
file. An already-exported env var always wins over `.env`. Config holds the
non-secret monitor id + Statuspage component id, never these secret values:

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

⚠ `decide` publishes **recoveries with no human gate**
(`core/services/decide.py`), so any loop run wired to the real publisher can post
to the LIVE public Statuspage. Guard demo/local loop runs with a config-only
publish guard (no `statuspage_component_id` → empty mapping → `LoggingPublisher`)
*and* `CONFIG_DIR` on the API process, which is a separate process reading its own
config.

### Throwaway DynamoDB for local/CI runs

Under `pytest`, the session-scoped `dynamo_local` fixture
(`backend/tests/conftest.py`) starts an in-memory `amazon/dynamodb-local` container
if Docker is available, or reuses `DYNAMO_ENDPOINT_URL` if set, otherwise skips
DynamoDB-gated tests. `clean_dynamo_tables` deletes and re-creates the tables
before each test. Known defect: the ephemeral host port the fixture picks is mapped
by Docker but not always routable on Windows — set `DYNAMO_ENDPOINT_URL` to a
fixed-port container to work around it (STORY-179).

## Run the app locally

Full local stack: DynamoDB Local + the API server (uvicorn) + the live pull-loop +
the frontend dev server.

1. Start DynamoDB Local — the `docker run` in Key commands (host port 8001, leaving
   8000 for the API).
2. Export `DYNAMO_ENDPOINT_URL="http://localhost:8001"` (or put it in a repo-root `.env`).
3. `python scripts/create_tables.py`
4. Start the API on port 8000 (serves `/api/v1/*`; the boot-time lifespan seed reads
   `config/apps` and populates components):
   `python -m uvicorn src.composition.asgi:app --port 8000`
5. SECOND terminal — the live loop (needs the Dynatrace/Statuspage secrets, exported
   or in the same `.env`; read the publish warning above first):
   `python -m src.composition.run`
6. THIRD terminal: `cd frontend && npm run dev`

## Tooling inventory

| Tool          | Version (verified 2026-07-29) | Note                                    |
| ------------- | ----------------------------- | --------------------------------------- |
| Python        | 3.13.9 (repo `.venv`)         | runtime                                 |
| pip           | 26.1.2                        | package management                      |
| ruff          | 0.15.20                       | DoD: `ruff check` + `ruff format`       |
| cfn-lint      | 1.53.0                        | DoD: CloudFormation validation          |
| import-linter | invoked as a module, not the exe | DoD: the eight zone contracts        |
| pytest        | —                             | DoD: must exit 0                        |
| Docker        | 28.5.2                        | DynamoDB Local for dev/CI               |
| Node / npm    | 24.11.1 / 11.6.2              | the three frontend DoD commands         |
| uvicorn       | dev dependency                | local ASGI server                       |

Runtime dependencies (boto3, httpx, python-dotenv, pydantic, FastAPI) are declared
in `pyproject.toml` — that file, not this one, is the source of truth for versions.
No `psql` client and no SQL database is used.

## Deployed topology (STORY-089)

Deployed to AWS **us-east-1**, account `065317679010`, as CloudFormation stack
`uptime-monitor` (from `infra/stack.yaml`; procedure: `docs/deploy-runbook.md`).
Full detail: `docs/scrum/wiki/deployment-topology.md`.

| Piece          | Value                                                                   |
| -------------- | ----------------------------------------------------------------------- |
| Public URL     | `https://d3ukiib1iqmbxb.cloudfront.net` (SPA + same-origin `/api/*`)    |
| ECS cluster    | `uptime-monitor-cluster` — services `uptime-monitor-api` (behind the ALB) + `uptime-monitor-loop` (singleton) |
| Image          | `065317679010.dkr.ecr.us-east-1.amazonaws.com/uptime-monitor-repo:latest` |
| Tables         | `uptime-monitor-observations`, `uptime-monitor-control` (DeletionPolicy Retain) |
| Secrets (names)| `uptime-monitor-dynatrace-secrets` (`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`); `uptime-monitor-statuspage-secrets` (`STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY`) — values ONLY in Secrets Manager |
| Plain env vars | `AWS_REGION`, `DYNAMO_OBSERVATIONS_TABLE`, `DYNAMO_CONTROL_TABLE` (injected by task defs) |
| Logs           | `/ecs/uptime-monitor-api`, `/ecs/uptime-monitor-loop` (CloudWatch, 14 days) |

**Status: last verified healthy 2026-07-17 (STORY-089). Re-checked 2026-07-29 —
`/api/v1/health` returned 503 and AWS credentials were expired, so the cause is
unconfirmed.** CloudFront answers, so the origin is unhealthy; the likeliest cause
is the 22:00 IST reaper stopping ECS tasks that lost their `c7n-keep=true` tag.
Re-verify before trusting anything in this section:

```
curl https://d3ukiib1iqmbxb.cloudfront.net/api/v1/health          # expect 200
aws ecs describe-services --cluster uptime-monitor-cluster \
  --services uptime-monitor-api uptime-monitor-loop               # expect both 1/1
```

Company account rules (region lock us-east-1, `c7n-keep=true` tagging against the
reaper): `docs/deploy-runbook.md` Prerequisites.

## History — superseded, kept so it isn't re-litigated

These were true once and are documented here only because the code still carries
their shape. None is current guidance.

- **Railway + Vercel** were the original deploy targets (dossier §3). STORY-089
  moved everything to AWS ECS + CloudFront. Two stale code comments named them
  (`composition/run.py`, `frontend/src/api/client.ts`); STORY-181 corrected both.
- **Neon Postgres + Alembic** were the persistence layer until STORY-087 migrated
  everything to DynamoDB. Both are retired; `sqlalchemy`/`psycopg` now appear only
  as *forbidden* modules in the import-linter config.
- **Design lineage.** `DESIGN-linear.app.md` (repo root) guided the sprint-25 shell;
  sprint 38 retuned the palette/type-scale values to an imported *Operator
  Dashboard* mock while keeping that shape (7-status health palette, four shared
  primitives). The current reference is the new UI above. The file stays on disk
  because sprint history cites it.
- **Three rejected UI attempts** — sprints 59 and 60 rejected by the PO, sprint 61
  aborted; all three remain unmerged on their branches. That is *why* the frontend
  work now leads with a styleguide + shell checkpoint instead of building six pages
  first, and why the reference is a UI the PO built themselves.
- **`sample_mode`** was the pre-demo-engine way to fake vendor data. Inert since the
  trial expired; removal is STORY-155.
- **`api/v1/_shared/middleware.py`** used to name STORY-017 as its intended CORS occupant.
  STORY-017 is archived and was about deployment topology, not CORS. STORY-181 corrected the
  docstring to state directly that no CORS is required (dev: Vite proxy; prod: same-origin
  behind CloudFront) and left the file as a documented seam for future middleware (e.g.
  authentication, still unassigned).
- **The first frontend attempt** (sprints 23–24, built to a since-removed
  `DESIGN-airtable.md`) was fully reverted in `521764c`. Nothing in `frontend/`
  descends from it. See `docs/scrum/wiki/frontend-zone.md`.
