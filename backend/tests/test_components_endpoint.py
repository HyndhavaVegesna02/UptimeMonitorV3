from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain.component import Component
from src.core.domain.status import ComponentStatus
from tests.fakes import FakeComponentRepository, FakeProposalRepository


def test_get_components_empty():
    component_repo = FakeComponentRepository()
    proposal_repo = FakeProposalRepository()
    app = create_app(component_repo=component_repo, proposal_repo=proposal_repo)
    client = TestClient(app)

    response = client.get("/api/v1/components")
    assert response.status_code == 200
    assert response.json() == []


def test_get_components_populated():
    comp1 = Component(
        id="c1", name="Comp 1", status=ComponentStatus.OPERATIONAL, app_id="app-1"
    )
    comp2 = Component(
        id="c2", name="Comp 2", status=ComponentStatus.DEGRADED, app_id="app-1"
    )
    component_repo = FakeComponentRepository(components=[comp1, comp2])
    proposal_repo = FakeProposalRepository()
    app = create_app(component_repo=component_repo, proposal_repo=proposal_repo)
    client = TestClient(app)

    response = client.get("/api/v1/components")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0] == {"id": "c1", "name": "Comp 1", "status": "operational"}
    assert data[1] == {"id": "c2", "name": "Comp 2", "status": "degraded"}
