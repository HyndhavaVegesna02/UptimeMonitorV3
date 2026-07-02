"""ASGI entrypoint for local/dev serving (dossier §17, STORY-042).

Run with: ``uvicorn src.composition.asgi:app --port 8000``

Exposes a module-level, fully-wired FastAPI ``app`` built via the same
`create_app(...)` composition root used elsewhere (`src.composition.app`).
Reads ``DATABASE_URL`` from the environment (the pooled Neon connection —
see `src.composition.settings.load_settings`) and the topology config from
`config/apps` (the `settings.config_dir` default) so the boot-time lifespan
seed runs and components are populated before the first request.

Import-time note: importing this module builds a real SQLAlchemy engine, so
``DATABASE_URL`` must already be set in the environment before import. This
is fine for `uvicorn` (which sets up the environment first) but callers such
as tests must set `DATABASE_URL` before importing this module — never import
it at collection time without a DB (see `backend/tests/test_asgi.py`).
"""

from src.composition.app import create_app

app = create_app()
"""The fully-wired FastAPI application, mounted at `/api/v1` (dossier §17)."""
