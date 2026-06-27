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
| Import boundary     | `lint-imports` (3 contracts; must exit 0) |
| Schema FK-direction | `python scripts/check_fk_direction.py` (reads `DATABASE_URL`; must exit 0) |
| Run migrations      | `alembic upgrade head` (reads `DATABASE_URL_DIRECT`; must exit 0) |
| Start throwaway DB  | `python scripts/dev_db.py up` (starts + migrates + prints both URLs) |
| Stop throwaway DB   | `python scripts/dev_db.py down` (removes the container) |
| Lint code           | `ruff check .` (must exit 0)               |
| Format check        | `ruff format --check .` (must exit 0)      |

`src` is the importable top-level package (it lives at `backend/src`, exposed via
`package-dir = {"" = "backend"}` in `pyproject.toml`).

The six DoD gate commands are `pytest`, `lint-imports`,
`python scripts/check_fk_direction.py`, `alembic upgrade head`, `ruff check`, and `ruff format`. All six are
live as of STORY-033. `lint-imports` enforces the three dossier §4 contracts
(core-independence, core-internal-layering, adapters-independence);
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
| git               | configured                    | version control                           |

No `psql` client is installed. No Neon/Dynatrace/Statuspage credentials are
needed during Sprint 0.
