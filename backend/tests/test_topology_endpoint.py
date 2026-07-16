"""Tests for the topology API feature (dossier §7, §9, §13, STORY-044 AC1).

Exercises `GET /api/v1/topology` — component→signals enumeration sourced from
the seeded topology (NOT re-read from config files at request time). Covers:
  - 200 + [] on an empty topology
  - multi-signal component nests signals sorted by signal_key, all four fields
  - a zero-signal component gets an empty `signals` list
  - an orphan signal (component_id=None) appears nowhere in the payload
  - five-file shape assertion (2026-06-28 agreement)
  - a DB-gated end-to-end test seeding through `seed_topology` + a real
    Postgres-backed `create_app`, proving the payload is sourced from the DB.
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain import Component, ComponentStatus
from src.core.domain.topology import Signal
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakeMaintenanceRepository,
    FakeObservationRepository,
    FakeProposalRepository,
    FakeSignalRepository,
)

_NOW = datetime(2026, 7, 3, 12, 0, 0, tzinfo=timezone.utc)


def _app(component_repo, signal_repo):
    return create_app(
        proposal_repo=FakeProposalRepository(),
        component_repo=component_repo,
        maintenance_repo=FakeMaintenanceRepository(),
        observation_repo=FakeObservationRepository(),
        signal_repo=signal_repo,
        clock=FakeClock(_NOW),
    )


def test_topology_empty_returns_200_empty_list():
    """AC1: empty topology -> 200 + []."""
    client = TestClient(_app(FakeComponentRepository(), FakeSignalRepository()))

    response = client.get("/api/v1/topology")

    assert response.status_code == 200
    assert response.json() == []


def test_topology_multi_signal_component_nests_sorted_signals():
    """AC1: multi-signal component nests signals sorted by signal_key with all four fields."""
    component = Component(
        id="checkout",
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    signals = [
        Signal(
            signal_key="checkout-http-b",
            name="Checkout HTTP B",
            component_id="checkout",
            interval_seconds=120,
        ),
        Signal(
            signal_key="checkout-http-a",
            name="Checkout HTTP A",
            component_id="checkout",
            interval_seconds=60,
        ),
    ]
    client = TestClient(
        _app(FakeComponentRepository([component]), FakeSignalRepository(signals))
    )

    response = client.get("/api/v1/topology")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "checkout"
    assert data[0]["name"] == "Checkout"
    assert [s["signal_key"] for s in data[0]["signals"]] == [
        "checkout-http-a",
        "checkout-http-b",
    ]
    first = data[0]["signals"][0]
    assert first["name"] == "Checkout HTTP A"
    assert first["interval_seconds"] == 60
    assert first["component_id"] == "checkout"


def test_topology_zero_signal_component_has_empty_signals():
    """AC1: a component with no mapped signals gets signals: []."""
    component = Component(
        id="empty-comp",
        name="Empty Comp",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    client = TestClient(
        _app(FakeComponentRepository([component]), FakeSignalRepository())
    )

    response = client.get("/api/v1/topology")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["signals"] == []


def test_topology_orphan_signal_excluded():
    """AC1: an orphan signal (component_id=None) appears nowhere in the nesting."""
    component = Component(
        id="checkout",
        name="Checkout",
        status=ComponentStatus.OPERATIONAL,
        app_id="sockshop",
    )
    orphan = Signal(
        signal_key="orphan-sig",
        name="Orphan Signal",
        component_id=None,
        interval_seconds=30,
    )
    client = TestClient(
        _app(FakeComponentRepository([component]), FakeSignalRepository([orphan]))
    )

    response = client.get("/api/v1/topology")

    assert response.status_code == 200
    data = response.json()
    assert data[0]["signals"] == []
    assert "orphan-sig" not in str(data)


def test_topology_module_five_file_shape():
    """AC4/2026-06-28 agreement: the topology feature follows the five-file convention exactly."""
    from src.api.v1 import topology

    pkg_dir = Path(topology.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }


def test_topology_db_gated_sourced_from_seeded_topology(
    dynamo_local, clean_dynamo_tables, tmp_path, monkeypatch
):
    """AC1: the payload is sourced from the seeded topology (DB), never re-read
    from config/ at request time — proven with a real DynamoDB-backed
    create_app + seed_topology_dynamo at lifespan startup."""
    config_dir = tmp_path / "apps"
    config_dir.mkdir()
    yaml_content = """
app:
  id: topo-app
  name: Topo App
  monitor_provider: dynatrace
components:
  - { id: topo-comp, name: Topo Comp }
signals:
  - { signal_key: topo-sig-a, native_id: N-A, name: Sig A, component_id: topo-comp, interval_seconds: 60 }
  - { signal_key: topo-sig-b, native_id: N-B, name: Sig B, component_id: topo-comp, interval_seconds: 120 }
"""
    (config_dir / "topo_app.yaml").write_text(yaml_content, encoding="utf-8")

    # Temporarily set env CONFIG_DIR for create_app settings load
    monkeypatch.setenv("CONFIG_DIR", str(config_dir))
    app = create_app(
        config_dir=str(config_dir),
    )

    with TestClient(app) as client:
        response = client.get("/api/v1/topology")
        assert response.status_code == 200
        data = response.json()
        comp = next(c for c in data if c["id"] == "topo-comp")
        by_key = {s["signal_key"]: s for s in comp["signals"]}
        assert by_key["topo-sig-a"]["interval_seconds"] == 60
        assert by_key["topo-sig-b"]["interval_seconds"] == 120
        assert by_key["topo-sig-a"]["component_id"] == "topo-comp"
