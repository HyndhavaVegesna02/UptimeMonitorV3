"""ASGI entrypoint for local/dev serving (dossier §17, STORY-042, STORY-043, STORY-087).

Run with: ``uvicorn src.composition.asgi:app --port 8000``

Exposes a module-level, fully-wired FastAPI ``app`` built via the same
`create_app(...)` composition root used elsewhere (`src.composition.app`).
Since the DynamoDB cutover (STORY-087) `create_app()` constructs the DynamoDB
persistence adapters from settings (``AWS_REGION`` /
``DYNAMO_OBSERVATIONS_TABLE`` / ``DYNAMO_CONTROL_TABLE`` / optional
``DYNAMO_ENDPOINT_URL`` for DynamoDB Local — see
`src.composition.settings.load_settings` and `src.composition.dynamo`).
It builds NO SQLAlchemy engine and reads NO ``DATABASE_URL``. The topology
config is read from `config/apps` (the `settings.config_dir` default) so the
boot-time lifespan seed populates the control table before the first request.

A gitignored repo-root ``.env`` is still loaded into the environment first
(see the `load_dotenv()` call below, STORY-043) so local dev can supply
``DYNAMO_ENDPOINT_URL`` and the Dynatrace/Statuspage secrets from that file
rather than exporting them; an already-exported var always wins (AC3).
"""

from dotenv import load_dotenv

from src.composition.app import create_app

# STORY-043: load a repo-root `.env` BEFORE create_app() reads settings (via
# `load_settings`), so `uvicorn src.composition.asgi:app` — run per the
# documented "Run the app locally" recipe (CLAUDE.md) from the repo root —
# can supply DYNAMO_ENDPOINT_URL and the Dynatrace/Statuspage secrets from a
# gitignored `.env` file. No explicit path is passed: `load_dotenv()`'s
# default discovery walks upward from THIS file's own location (not the
# process CWD) to find the repo-root `.env` — the assumption is that the repo
# layout on disk is intact. Default `override=False` semantics mean an
# already-exported var always wins (AC3), so production (no `.env` file
# present) is unaffected.
load_dotenv()

app = create_app()
"""The fully-wired FastAPI application, mounted at `/api/v1` (dossier §17)."""
