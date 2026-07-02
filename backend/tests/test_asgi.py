"""Servability tests for the ASGI entrypoint (STORY-042, dossier §17).

Proves the wiring `uvicorn src.composition.asgi:app` depends on: a
fully-wired FastAPI app, built via the same `create_app(...)` composition
root used elsewhere, serves real `/api/v1/*` routes once the boot-time
topology seed (reading `config/apps`) has run.

Import-time caveat (see docs/scrum/sprints/2026-07-02-sprint-28/plan.md T2):
`src.composition.asgi` builds a real SQLAlchemy engine at import time via
`create_app()`, which requires `DATABASE_URL` to already be set. This module
must NEVER import `src.composition.asgi` at collection time (module level) —
only inside a test body, after the `migrated_db` fixture has set
`DATABASE_URL` in the environment.
"""

import importlib

import psycopg
import pytest
from fastapi.testclient import TestClient
from src.composition.app import create_app


@pytest.fixture
def clean_topology(migrated_db):
    """Truncate topology tables before and after the test (STORY-039 pattern).

    Mirrors the `clean_topology` fixture in test_seed.py: this test seeds the
    REAL `config/apps` topology (not a tmp_path fixture config), so it must
    leave the shared session-scoped DB exactly as it found it.
    """
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE apps, components, signals CASCADE;")
        conn.commit()
    yield
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE apps, components, signals CASCADE;")
        conn.commit()


def test_create_app_serves_real_components_route(migrated_db, clean_topology):
    """AC3: create_app(database_url=..., config_dir="config/apps") — the same
    wiring the ASGI entrypoint uses — serves a real HTTP route.

    GET /api/v1/components returns 200 with the components seeded from the
    real repo-root config/apps/httpcheck.yaml at boot (lifespan startup).
    """
    app = create_app(database_url=migrated_db.database_url, config_dir="config/apps")

    with TestClient(app) as client:
        response = client.get("/api/v1/components")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        ids = {component["id"] for component in data}
        assert "http-check" in ids


def test_asgi_module_exposes_app(migrated_db, clean_topology, monkeypatch):
    """AC2: `src.composition.asgi` exposes a module-level `app` built via
    `create_app(...)`, reading DATABASE_URL from the environment.

    Imported INSIDE the test body (never at module top) so the real-engine
    build only happens once `migrated_db` has set DATABASE_URL — see the
    import-time caveat in the module docstring above.
    """
    monkeypatch.setenv("DATABASE_URL", migrated_db.database_url)

    asgi = importlib.import_module("src.composition.asgi")
    importlib.reload(asgi)  # in case a prior test in the process imported it

    from fastapi import FastAPI

    assert isinstance(asgi.app, FastAPI)

    with TestClient(asgi.app) as client:
        response = client.get("/api/v1/components")
        assert response.status_code == 200
