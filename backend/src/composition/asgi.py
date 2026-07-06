"""ASGI entrypoint for local/dev serving (dossier §17, STORY-042, STORY-043).

Run with: ``uvicorn src.composition.asgi:app --port 8000``

Exposes a module-level, fully-wired FastAPI ``app`` built via the same
`create_app(...)` composition root used elsewhere (`src.composition.app`).
Reads ``DATABASE_URL`` from the environment (the pooled Neon connection —
see `src.composition.settings.load_settings`) and the topology config from
`config/apps` (the `settings.config_dir` default) so the boot-time lifespan
seed runs and components are populated before the first request. A
gitignored repo-root ``.env`` is loaded into the environment first (see the
`load_dotenv()` call below, STORY-043), so ``DATABASE_URL`` can come from
that file instead of requiring it to be exported into the shell.

Import-time note: importing this module builds a real SQLAlchemy engine, so
``DATABASE_URL`` must already be set in the environment (or resolvable from a
repo-root `.env`) before import. This is fine for `uvicorn` (which sets up
the environment first) but callers such as tests must set `DATABASE_URL`
before importing this module — never import it at collection time without a
DB (see `backend/tests/test_asgi.py`).
"""

from dotenv import load_dotenv

from src.composition.app import create_app

# STORY-043: load a repo-root `.env` BEFORE create_app() reads DATABASE_URL
# (via `load_settings`), so `uvicorn src.composition.asgi:app` — run per the
# documented "Run the app locally" recipe (CLAUDE.md) from the repo root —
# can supply DATABASE_URL from a gitignored `.env` file. No explicit path is
# passed: `load_dotenv()`'s default discovery walks upward from THIS file's
# own location (not the process CWD) to find the repo-root `.env` — the
# assumption is that the repo layout on disk is intact. Default
# `override=False` semantics mean an already-exported var always wins (AC3),
# so production (Railway, no `.env` file present) is unaffected.
load_dotenv()

app = create_app()
"""The fully-wired FastAPI application, mounted at `/api/v1` (dossier §17)."""
