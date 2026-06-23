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
directly on Windows: `.venv/Scripts/python.exe`).

| Task                | Command                                  |
| ------------------- | ---------------------------------------- |
| Create venv         | `python -m venv .venv`                    |
| Install (editable)  | `.venv/Scripts/python.exe -m pip install -e ".[dev]"` |
| Run tests           | `pytest`                                  |
| Verify zone imports | `python -c "import src.core, src.adapters, src.composition, src.api"` |

`src` is the importable top-level package (it lives at `backend/src`, exposed via
`package-dir = {"" = "backend"}` in `pyproject.toml`). Import-linter contracts and
Alembic arrive in later stories.

## Tooling inventory

| Tool              | Version / note                | Purpose                                   |
| ----------------- | ----------------------------- | ----------------------------------------- |
| Python            | 3.13.9 (miniconda)            | runtime                                   |
| pip               | 25.2                          | package management                        |
| pytest            | test runner (DoD gate)        | `pytest` must exit 0                       |
| import-linter     | `lint-imports` (from STORY-002)| enforces zone dependency boundaries       |
| SQLAlchemy 2 / Alembic | (Alembic wired in STORY-003) | ORM + migrations                       |
| Docker            | 28.5.2                        | throwaway Postgres for migration/FK checks|
| git               | configured                    | version control                           |

No `psql` client is installed. No Neon/Dynatrace/Statuspage credentials are
needed during Sprint 0.
