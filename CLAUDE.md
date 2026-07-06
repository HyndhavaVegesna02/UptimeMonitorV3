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

### The frontend zone (dossier §17, STORY-015a)

`frontend/` is a separate Vite + React + TypeScript (strict) SPA — the
operator-cockpit "internal dashboard" surface (dossier §17, "two surfaces,
not one"; the other surface is the public Statuspage). It is isolated from
the Python backend: no backend source import, no shared build step; the six
backend DoD commands never touch it and vice versa.

```
frontend/
├── src/
│   ├── styles/       # tokens.css (theme-scoped CSS custom properties) + global.css
│   ├── theme/         # theme resolution (system pref + localStorage override), ThemeProvider/useTheme
│   ├── components/    # shell primitives: Button, StatusBadge, Panel, Loading/Error/EmptyState
│   ├── nav/            # top nav (six-tab IA) + routing table (tabs.ts)
│   ├── pages/          # one placeholder per tab (015b-015g fill in real content)
│   ├── api/             # typed fetch client (client.ts), DTO types mirroring backend/src/api/v1/*/models.py
│   ├── features/        # per-tab feature code (e.g. features/dashboard/ComponentsProbe.tsx)
│   ├── mocks/            # MSW handlers + node server (the only mocked I/O edge in frontend tests)
│   └── test/              # Vitest setup (jest-dom matchers, MSW server lifecycle)
├── index.html            # pre-paint inline theme-resolution script (no flash)
└── vite.config.ts         # dev proxy (/api -> http://localhost:8000) + Vitest config
```

Design reference: `DESIGN-linear.app.md` (repo root) — a guide to adapt, not
a copy target; see `docs/scrum/sprints/2026-07-02-sprint-25/plan.md` for the
binding design brief (token values, accent discipline, health palette, type
scale) that STORY-015a built to. `frontend/README.md` has the day-to-day
quick reference.

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
| database       | Neon serverless Postgres, via the pooled PgBouncer connection      |
| observability  | Dynatrace synthetic monitors; results read from Grail via DQL      |
| demo app       | Sock Shop on Railway — the replaceable monitored application       |
| publish target | Statuspage — a fixed core target (not swappable in V3 scope)       |

Python 3.13. Backend libraries: FastAPI, Pydantic v2, SQLAlchemy 2, Alembic,
psycopg 3.

## Key commands

Run from the repo root with the virtualenv active (or call the `.venv` binaries
directly on Windows: `.venv/Scripts/python.exe`, `.venv/Scripts/lint-imports.exe`).

| Task                | Command                                  |
| ------------------- | ---------------------------------------- |
| Create venv         | `python -m venv .venv`                    |
| Install (editable)  | `.venv/Scripts/python.exe -m pip install -e ".[dev]"` |
| Run tests           | `pytest`                                  |
| Verify zone imports | `python -c "import src.core, src.adapters, src.composition, src.api"` |
| Import boundary     | `lint-imports` (5 contracts; must exit 0) |
| Schema FK-direction | `python scripts/check_fk_direction.py` (reads `DATABASE_URL`; must exit 0) |
| Run migrations      | `alembic upgrade head` (reads `DATABASE_URL_DIRECT`; must exit 0) |
| Start throwaway DB  | `python scripts/dev_db.py up` (starts + migrates + prints both URLs) |
| Stop throwaway DB   | `python scripts/dev_db.py down` (removes the container) |
| Run live loop       | `python -m src.composition.run` (reads `.env`, runs e2e loop) |
| Lint code           | `ruff check .` (must exit 0)               |
| Format check        | `ruff format --check .` (must exit 0)      |

`src` is the importable top-level package (it lives at `backend/src`, exposed via
`package-dir = {"" = "backend"}` in `pyproject.toml`).

The six DoD gate commands are `pytest`, `lint-imports`,
`python scripts/check_fk_direction.py`, `alembic upgrade head`, `ruff check`, and `ruff format`. All six are
live as of STORY-033. `lint-imports` enforces the five contracts
(core-independence, core-internal-layering, adapters-independence, api-feature-independence, src-no-tests);
`check_fk_direction.py` enforces the dossier §9 schema spine boundary (no
spine→feature foreign key) by reading `information_schema` over `DATABASE_URL`;
`alembic upgrade head` applies the migrations at the repo top level;
`ruff check` and `ruff format` enforce the code style, import sorting, and formatting.

## Database & migrations (dossier §3, §4, §17)

Two distinct connection strings, two distinct env vars — never mix them:

| Env var               | Connection            | Used by                                      |
| --------------------- | --------------------- | -------------------------------------------- |
| `DATABASE_URL`        | Neon **pooled** (PgBouncer) | app runtime (`src.composition.settings`) and `scripts/check_fk_direction.py` |
| `DATABASE_URL_DIRECT` | Neon **direct** (non-pooled) | Alembic migrations (`migrations/env.py`) — DDL misbehaves through transaction pooling |

### Live-loop secrets (STORY-016 — read by `python -m src.composition.run`)

Read from the environment / a gitignored `.env` via `composition/settings.py::load_live_secrets()`
(never committed; config holds the non-secret monitor id + Statuspage component id, never these values):

| Env var               | Used for                                                          |
| --------------------- | ---------------------------------------------------------------- |
| `DYNATRACE_ENV_URL`   | Dynatrace tenant base URL (Grail DQL execute endpoint)           |
| `DYNATRACE_API_TOKEN` | Dynatrace platform token (scopes `storage:buckets:read storage:events:read`) |
| `STATUSPAGE_PAGE_ID`  | Statuspage page id                                               |
| `STATUSPAGE_API_KEY`  | Statuspage API token (→ `Settings.statuspage_api_token`)         |

Migrations are real, versioned from day one, and live at the **repo top level**
(`alembic.ini` + `migrations/`), NOT under `backend/`. Never `create_all`. They
run as a **separate release step** on the DIRECT connection; the app runtime uses
the POOLED connection.

URL dialect note: `migrations/env.py` (SQLAlchemy 2) needs the psycopg3 driver,
so it normalizes a bare `postgresql://…` to `postgresql+psycopg://…`. The
FK-direction check uses raw psycopg, which wants a plain libpq
`postgresql://…` URL (no `+psycopg`). So when both run against the same DB,
set `DATABASE_URL_DIRECT` to the `postgresql+psycopg://…` form and `DATABASE_URL`
to the plain `postgresql://…` form.

### Throwaway Postgres for local/CI runs (no Neon needed in Sprint 0)

**Standard way (STORY-019):** `scripts/dev_db.py` is the shared helper — it
replaces hand-rolling the `docker run` + wait-ready + `alembic upgrade head` +
two-URL dialect split sequence shown below. Use it for manual local runs of
the DB-gated DoD commands:

```bash
.venv/Scripts/python.exe scripts/dev_db.py up      # start + wait + migrate + print both URLs
# copy/export the two `export DATABASE_URL...` lines it prints, or pass
# --env-file path/to/.env to also write them to a dotenv file, then:
.venv/Scripts/python.exe scripts/check_fk_direction.py   # -> exit 0, no manual juggling
.venv/Scripts/alembic.exe upgrade head                   # -> exit 0
.venv/Scripts/python.exe scripts/dev_db.py down    # remove the container
```

Under `pytest`, the same logic is exposed as the session-scoped `migrated_db`
fixture (`backend/tests/conftest.py`): it reuses already-set
`DATABASE_URL`/`DATABASE_URL_DIRECT` if both are present (migrating to ensure
current), else spawns a throwaway `postgres:16` if Docker is available (one
per test session, on a free port, torn down in a finalizer even if a test
fails), else skips the DB-gated tests cleanly. DB-gated tests (e.g.
`backend/tests/test_spine_schema.py`) depend on this fixture instead of
rolling their own `skipif`/connection setup.

The manual one-liner that `scripts/dev_db.py` wraps (kept here for reference,
or for anyone who wants to drive Docker directly without the helper):

```bash
# one-liner to start a disposable Postgres (Docker 28.x):
docker run -d --name uptime_pg_test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=uptime -p 55432:5432 postgres:16
# wait until ready: docker exec uptime_pg_test pg_isready -U postgres

# migrations use the DIRECT URL (SQLAlchemy/psycopg3 dialect):
export DATABASE_URL_DIRECT="postgresql+psycopg://postgres:postgres@localhost:55432/uptime"
# the FK-direction check uses the pooled DATABASE_URL (plain libpq form):
export DATABASE_URL="postgresql://postgres:postgres@localhost:55432/uptime"

alembic upgrade head                 # apply migrations  -> exit 0
alembic downgrade base               # reverse to empty  -> exit 0
alembic upgrade head                 # re-apply          -> exit 0
python scripts/check_fk_direction.py # 0 FKs on baseline -> exit 0

docker rm -f uptime_pg_test          # clean up (never commit container/data)
```

## Run the app locally (dossier §17, STORY-042)

The full local stack is: throwaway Postgres + the API server (uvicorn) + the
live pull-loop (`python -m src.composition.run`) + the frontend dev server —
four processes sharing one `DATABASE_URL`. CORS is unneeded locally: the Vite
dev proxy makes the frontend same-origin (real CORS is enforced only in the
deployed topology — see "Deployed topology" below).

1. Start the throwaway DB (migrates and prints both URLs):
   `.venv/Scripts/python.exe scripts/dev_db.py up`
2. Export `DATABASE_URL` — the plain-libpq pooled form it printed (the
   direct/`+psycopg` form is only for Alembic/migrations, not needed here).
3. Start the API server on port 8000 (serves `/api/v1/*`; the boot-time
   lifespan seed reads `config/apps` and populates components):
   `.venv/Scripts/python.exe -m uvicorn src.composition.asgi:app --port 8000`
4. In a SECOND terminal (same `DATABASE_URL`), run the live loop to populate
   observations/proposals/publications — needs the Dynatrace/Statuspage `.env`
   secrets (see "Live-loop secrets" above): `python -m src.composition.run`
5. In a THIRD terminal: `cd frontend && npm run dev` — the Vite proxy now
   reaches a real backend on :8000; no more `ECONNREFUSED`.

The API server and the live loop are two independent, long-running processes
— stopping one doesn't stop the other, and both must point at the same
`DATABASE_URL`. `python scripts/dev_db.py down` tears down the throwaway
Postgres container when done.

## Deployed topology (dossier §17, STORY-017)

Backend on Railway as TWO long-running services from this one repo, both
reading the POOLED `DATABASE_URL`; frontend on Vercel. Full numbered PO
console steps (project/service creation, env var entry, healthcheck,
verification) live in `docs/DEPLOY.md` — this section is the quick-reference
summary CLAUDE.md's command-sync agreement requires.

| Process  | Command                                                        | Reads                       |
| -------- | --------------------------------------------------------------- | ---------------------------- |
| release  | `alembic upgrade head` (Railway `preDeployCommand`, `railway.toml`) | `DATABASE_URL_DIRECT` |
| `api`    | `uvicorn src.composition.asgi:app --host 0.0.0.0 --port $PORT`  | `DATABASE_URL`, `CORS_ALLOWED_ORIGINS` |
| `worker` | `python -m src.composition.run`                                 | `DATABASE_URL`, `DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`, `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY` |

- The release step runs ONCE, before `api` serves, on the DIRECT connection
  (dialect note above); a nonzero exit halts the deploy and the previous
  container keeps serving (AC3 fail-safe — Railway's own release-command
  semantics, no custom code). `worker` has no release step of its own.
- Both `api` and `worker` seed topology at boot from `config/apps/*.yaml`;
  the seed is idempotent upserts, so double-seeding across both processes
  (or a restart) is always safe.
- Railway config-as-code lives at the repo-root `railway.toml` — built to
  [Config as Code](https://docs.railway.com/config-as-code) and its
  [reference](https://docs.railway.com/reference/config-as-code). It
  expresses the `api` service only (build, release, start, healthcheck);
  `worker`'s start command is a console-only field (`docs/DEPLOY.md` Part A4)
  since Railway has no native "two start commands, one config file" shape
  for services sharing a repo (confirmed against Railway's monorepo doc and
  the "config-as-code always overrides the dashboard" rule).
- `frontend/vercel.json` rewrites `/api/*` to the Railway `api` origin (a
  placeholder the runbook has the PO fill in — Vercel's config file is
  static, no env-var substitution — verified against
  [Vercel project configuration](https://vercel.com/docs/project-configuration))
  and falls back every other path to `/index.html` for the six-tab
  client-side router (`App.tsx`'s `BrowserRouter`).
  `frontend/src/api/client.ts::API_BASE_URL` stays `'/api'`, unchanged.
- CORS: `composition/app.py::create_app` wires `CORSMiddleware` with an
  allowlist read from `CORS_ALLOWED_ORIGINS` (comma-separated env var name
  only; unset defaults to `http://localhost:5173` for local dev). Defense-in-
  depth behind the Vercel rewrite (the browser stays same-origin through it)
  per the 2026-06-23 agreement. `allow_credentials=False` — no cookie/session
  auth exists yet.
- Secrets hygiene (AC5): no secret VALUE lives in this repo at any commit —
  every table above lists env var NAMES only; values are entered directly
  into Railway service Variables by the PO.

## Tooling inventory

| Tool              | Version / note                | Purpose                                   |
| ----------------- | ----------------------------- | ----------------------------------------- |
| Python            | 3.13.9 (miniconda)            | runtime                                   |
| pip               | 25.2                          | package management                        |
| pytest            | test runner (DoD gate)        | `pytest` must exit 0                       |
| import-linter     | `lint-imports` (live, STORY-002)| enforces zone dependency boundaries (DoD)|
| FK-direction check| `scripts/check_fk_direction.py` (live, STORY-002)| enforces schema spine boundary (DoD)|
| SQLAlchemy 2 / Alembic | live (STORY-003); `alembic upgrade head` (DoD) | ORM + migrations at repo top level |
| Docker            | 28.5.2                        | throwaway Postgres for migration/FK checks|
| `scripts/dev_db.py` | live (STORY-019)            | shared throwaway-DB helper (CLI `up`/`down`) + the `migrated_db` pytest session fixture |
| ruff              | live (STORY-033); `ruff check` + `ruff format` (DoD) | code style, sorting, and formatting |
| uvicorn[standard] | live (STORY-042); dev dependency | local ASGI dev server — `uvicorn src.composition.asgi:app` |
| httpx             | runtime dependency             | HTTP library for query and statuspage executors |
| git               | configured                    | version control                           |

No `psql` client is installed. Neon/Dynatrace/Statuspage credentials are read from `.env` or environment variables for the live loop.
