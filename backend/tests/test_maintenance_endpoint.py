"""Tests for the maintenance API feature (dossier §13, §17)."""

from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pytest

from src.composition.app import create_app
from src.core.domain.maintenance import MaintenanceWindow
from tests.fakes import FakeMaintenanceRepository, FakeProposalRepository, FakeComponentRepository


def test_get_maintenance_empty():
    maintenance_repo = FakeMaintenanceRepository()
    app = create_app(
        maintenance_repo=maintenance_repo,
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
    )
    client = TestClient(app)

    response = client.get("/api/v1/maintenance")
    assert response.status_code == 200
    assert response.json() == []


def test_get_maintenance_with_windows():
    w1 = MaintenanceWindow(
        id=1,
        component_id="checkout",
        starts_at=datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc),
        ends_at=datetime(2026, 6, 28, 14, 0, 0, tzinfo=timezone.utc),
        reason="Update",
    )
    maintenance_repo = FakeMaintenanceRepository(windows=[w1])
    app = create_app(
        maintenance_repo=maintenance_repo,
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
    )
    client = TestClient(app)

    response = client.get("/api/v1/maintenance")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["component_id"] == "checkout"
    assert data[0]["starts_at"].replace("+00:00", "Z") == "2026-06-28T12:00:00Z"
    assert data[0]["ends_at"].replace("+00:00", "Z") == "2026-06-28T14:00:00Z"
    assert data[0]["reason"] == "Update"


def test_post_maintenance_valid():
    maintenance_repo = FakeMaintenanceRepository()
    app = create_app(
        maintenance_repo=maintenance_repo,
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
    )
    client = TestClient(app)

    payload = {
        "component_id": "checkout",
        "starts_at": "2026-06-28T12:00:00Z",
        "ends_at": "2026-06-28T14:00:00Z",
        "reason": "Database migration",
    }
    response = client.post("/api/v1/maintenance", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["component_id"] == "checkout"
    assert data["starts_at"].replace("+00:00", "Z") == "2026-06-28T12:00:00Z"
    assert data["ends_at"].replace("+00:00", "Z") == "2026-06-28T14:00:00Z"
    assert data["reason"] == "Database migration"

    # Verify persisted in repo
    windows = maintenance_repo.list_windows()
    assert len(windows) == 1
    assert windows[0].component_id == "checkout"


def test_post_maintenance_invalid_times():
    maintenance_repo = FakeMaintenanceRepository()
    app = create_app(
        maintenance_repo=maintenance_repo,
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
    )
    client = TestClient(app)

    payload = {
        "component_id": "checkout",
        "starts_at": "2026-06-28T14:00:00Z",
        "ends_at": "2026-06-28T12:00:00Z",  # ends_at < starts_at
        "reason": "Invalid",
    }
    response = client.post("/api/v1/maintenance", json=payload)
    assert response.status_code == 422


def test_post_maintenance_malformed():
    maintenance_repo = FakeMaintenanceRepository()
    app = create_app(
        maintenance_repo=maintenance_repo,
        proposal_repo=FakeProposalRepository(),
        component_repo=FakeComponentRepository(),
    )
    client = TestClient(app)

    # Missing ends_at (which is required)
    payload = {
        "component_id": "checkout",
        "starts_at": "2026-06-28T12:00:00Z",
        "reason": "Missing ends_at",
    }
    response = client.post("/api/v1/maintenance", json=payload)
    assert response.status_code == 422


def test_maintenance_module_five_file_shape():
    # AC5: the feature follows the five-file convention exactly.
    from pathlib import Path

    from src.api.v1 import maintenance

    pkg_dir = Path(maintenance.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }

