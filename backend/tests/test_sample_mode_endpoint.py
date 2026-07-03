"""Tests for the sample-mode API feature (dossier §13/§17, STORY-048 D3, AC2).

TEMPORARY feature — see docs/scrum/wiki/sample-mode.md for the REMOVAL
inventory; this whole file is deleted when sample-mode is removed.

Exercises `GET /api/v1/sample-mode` (current flag state) and
`PUT /api/v1/sample-mode` (set the flag). Covers:
  - GET default false (never-set)
  - PUT true -> GET true, PUT false -> GET false (idempotent round-trips)
  - PUT with a missing/invalid body -> 422
  - five-file shape assertion (2026-06-28 agreement)
  - a DB-gated round-trip through a real Postgres-backed create_app
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import psycopg
import pytest
from fastapi.testclient import TestClient
from src.composition.app import create_app
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakeMaintenanceRepository,
    FakeObservationRepository,
    FakeProposalRepository,
    FakeSampleModeRepository,
)

_NOW = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


def _app(sample_mode_repo):
    return create_app(
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
        maintenance_repo=FakeMaintenanceRepository(),
        observation_repo=FakeObservationRepository(),
        sample_mode_repo=sample_mode_repo,
        clock=FakeClock(_NOW),
    )


def test_get_sample_mode_default_false():
    """AC2: never-set flag -> GET returns enabled: false."""
    client = TestClient(_app(FakeSampleModeRepository()))

    response = client.get("/api/v1/sample-mode")

    assert response.status_code == 200
    assert response.json() == {"enabled": False}


def test_put_sample_mode_true_then_get_reads_true():
    """AC2: PUT true sets the flag; a subsequent GET reads it back true."""
    repo = FakeSampleModeRepository()
    client = TestClient(_app(repo))

    put_response = client.put("/api/v1/sample-mode", json={"enabled": True})
    assert put_response.status_code == 200
    assert put_response.json() == {"enabled": True}

    get_response = client.get("/api/v1/sample-mode")
    assert get_response.json() == {"enabled": True}


def test_put_sample_mode_false_then_get_reads_false():
    """AC2: PUT false sets the flag; a subsequent GET reads it back false."""
    repo = FakeSampleModeRepository()
    repo.set_enabled(True)
    client = TestClient(_app(repo))

    put_response = client.put("/api/v1/sample-mode", json={"enabled": False})
    assert put_response.status_code == 200
    assert put_response.json() == {"enabled": False}

    get_response = client.get("/api/v1/sample-mode")
    assert get_response.json() == {"enabled": False}


def test_put_sample_mode_is_idempotent():
    """D2: setting the same value twice succeeds silently (no error)."""
    repo = FakeSampleModeRepository()
    client = TestClient(_app(repo))

    first = client.put("/api/v1/sample-mode", json={"enabled": True})
    second = client.put("/api/v1/sample-mode", json={"enabled": True})

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == {"enabled": True}


def test_put_sample_mode_missing_body_field_is_422():
    """AC2: a missing `enabled` field -> 422 (FastAPI/Pydantic body validation)."""
    client = TestClient(_app(FakeSampleModeRepository()))

    response = client.put("/api/v1/sample-mode", json={})

    assert response.status_code == 422


def test_put_sample_mode_invalid_body_type_is_422():
    """AC2: a non-boolean `enabled` value -> 422."""
    client = TestClient(_app(FakeSampleModeRepository()))

    response = client.put("/api/v1/sample-mode", json={"enabled": "not-a-bool"})

    assert response.status_code == 422


def test_sample_mode_module_five_file_shape():
    """2026-06-28 agreement: the sample_mode feature follows the five-file
    convention exactly."""
    from src.api.v1 import sample_mode

    pkg_dir = Path(sample_mode.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }


@pytest.fixture
def clean_sample_mode(migrated_db):
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE sample_mode;")
        conn.commit()
    yield
    with psycopg.connect(migrated_db.database_url) as conn:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE sample_mode;")
        conn.commit()


def test_sample_mode_db_gated_round_trip(migrated_db, clean_sample_mode):
    """AC2: PUT true against a REAL Postgres-backed create_app; a fresh GET
    reads it back true, proving the flag round-trips through the database
    (not just an injected fake)."""
    app = create_app(database_url=migrated_db.database_url)

    with TestClient(app) as client:
        put_response = client.put("/api/v1/sample-mode", json={"enabled": True})
        assert put_response.status_code == 200

        get_response = client.get("/api/v1/sample-mode")
        assert get_response.status_code == 200
        assert get_response.json() == {"enabled": True}
