"""Tests for the ASGI application module and entrypoint (dossier §17, spec §8)."""

from __future__ import annotations

import importlib
from unittest.mock import patch

from fastapi.testclient import TestClient
from src.composition.app import create_app


def test_create_app_serves_real_components_route(dynamo_local, clean_dynamo_tables):
    """AC3: create_app(config_dir="config/apps") serves a real HTTP route.

    GET /api/v1/components returns 200 with the components seeded from the
    real repo-root config/apps/httpcheck.yaml at boot (lifespan startup).
    """
    app = create_app(config_dir="config/apps")

    with TestClient(app) as client:
        response = client.get("/api/v1/components")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        ids = {component["id"] for component in data}
        assert "http-check" in ids


def test_asgi_module_exposes_app(dynamo_local, clean_dynamo_tables, monkeypatch):
    """AC2: `src.composition.asgi` exposes a module-level `app` built via
    `create_app(...)`, reading DYNAMO_ENDPOINT_URL from the environment.
    """
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", dynamo_local.endpoint_url)

    with patch("dotenv.load_dotenv"):
        asgi = importlib.import_module("src.composition.asgi")
        importlib.reload(asgi)

    from fastapi import FastAPI

    assert isinstance(asgi.app, FastAPI)

    with TestClient(asgi.app) as client:
        response = client.get("/api/v1/components")
        assert response.status_code == 200


def test_asgi_module_loads_dotenv_before_create_app(
    dynamo_local, clean_dynamo_tables, monkeypatch
):
    """AC2 (STORY-043): importing `src.composition.asgi` loads a repo-root
    `.env` (via `dotenv.load_dotenv`) BEFORE `create_app()`.
    """
    monkeypatch.setenv("DYNAMO_ENDPOINT_URL", dynamo_local.endpoint_url)

    real_create_app = create_app
    call_order = []

    def _tracking_create_app(*args, **kwargs):
        call_order.append("create_app")
        return real_create_app(*args, **kwargs)

    with (
        patch(
            "dotenv.load_dotenv",
            side_effect=lambda *a, **k: call_order.append("load_dotenv"),
        ) as mock_load_dotenv,
        patch("src.composition.app.create_app", side_effect=_tracking_create_app),
    ):
        asgi = importlib.import_module("src.composition.asgi")
        importlib.reload(asgi)

    mock_load_dotenv.assert_called_once_with()
    assert call_order == ["load_dotenv", "create_app"]

    from fastapi import FastAPI

    assert isinstance(asgi.app, FastAPI)

    # Leave the module in a clean (unpatched) state
    with patch("dotenv.load_dotenv"):
        importlib.reload(asgi)
