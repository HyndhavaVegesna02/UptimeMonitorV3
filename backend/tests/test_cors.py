"""CORS wiring tests (dossier §17, STORY-017 AC2).

`create_app` (composition zone) wires `fastapi.middleware.cors.CORSMiddleware`
with an env-driven allowlist (`CORS_ALLOWED_ORIGINS_VAR`, comma-separated;
unset/empty -> localhost-dev-only default). These are REAL preflight/simple
requests against a fully-built `create_app()` (no DB needed — a
`FakeProposalRepository` is injected, same pattern as `test_app.py`), never
mocked middleware, per the sprint-35 conventions checklist.
"""

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.composition.settings import (
    CORS_ALLOWED_ORIGINS_VAR,
    DEFAULT_CORS_ALLOWED_ORIGINS,
)
from tests.fakes import FakeProposalRepository


def _client() -> TestClient:
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    return TestClient(app)


def test_allowed_origin_preflight_ok_and_acao_echoed(monkeypatch):
    allowed = "https://app.example.vercel.app"
    monkeypatch.setenv(CORS_ALLOWED_ORIGINS_VAR, allowed)
    client = _client()

    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": allowed,
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed


def test_allowed_origin_simple_request_echoes_acao(monkeypatch):
    allowed = "https://app.example.vercel.app"
    monkeypatch.setenv(CORS_ALLOWED_ORIGINS_VAR, allowed)
    client = _client()

    response = client.get("/api/v1/health", headers={"Origin": allowed})

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed


def test_disallowed_origin_gets_no_cors_grant(monkeypatch):
    monkeypatch.setenv(CORS_ALLOWED_ORIGINS_VAR, "https://app.example.vercel.app")
    client = _client()

    response = client.get(
        "/api/v1/health", headers={"Origin": "https://evil.example.com"}
    )

    # The request itself is not blocked server-side (CORS is a browser-enforced
    # contract), but no ACAO grant is issued for the disallowed origin.
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_no_origin_header_request_unaffected(monkeypatch):
    """Server-to-server calls (the Vercel rewrite's hot path) carry no Origin
    header — CORSMiddleware must not touch these requests at all."""
    monkeypatch.setenv(CORS_ALLOWED_ORIGINS_VAR, "https://app.example.vercel.app")
    client = _client()

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_unset_env_defaults_to_localhost_dev_only(monkeypatch):
    monkeypatch.delenv(CORS_ALLOWED_ORIGINS_VAR, raising=False)
    client = _client()

    default_origin = DEFAULT_CORS_ALLOWED_ORIGINS[0]
    allowed_response = client.get("/api/v1/health", headers={"Origin": default_origin})
    assert allowed_response.headers.get("access-control-allow-origin") == default_origin

    disallowed_response = client.get(
        "/api/v1/health", headers={"Origin": "https://app.example.vercel.app"}
    )
    assert "access-control-allow-origin" not in disallowed_response.headers
