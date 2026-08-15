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
    # STORY-147 AC5: group/description are additive — every pre-existing
    # Component() call site (like these two, unchanged) still constructs,
    # and the response now carries the two new fields as null (AC3) since
    # neither component declares them.
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
    assert data[0] == {
        "id": "c1",
        "name": "Comp 1",
        "status": "operational",
        "group": None,
        "description": None,
    }
    assert data[1] == {
        "id": "c2",
        "name": "Comp 2",
        "status": "degraded",
        "group": None,
        "description": None,
    }


def test_get_components_returns_group_and_description_when_present():
    """STORY-147 AC3: GET /api/v1/components returns group/description when
    the component declares them, and serializes as `null` — never `""` and
    never a placeholder — when absent. Both shapes in one response so the
    contrast is direct."""
    categorized = Component(
        id="c1",
        name="Comp 1",
        status=ComponentStatus.OPERATIONAL,
        app_id="app-1",
        group="commerce",
        description="Cart, payments and order placement",
    )
    uncategorized = Component(
        id="c2", name="Comp 2", status=ComponentStatus.DEGRADED, app_id="app-1"
    )
    component_repo = FakeComponentRepository(components=[categorized, uncategorized])
    proposal_repo = FakeProposalRepository()
    app = create_app(component_repo=component_repo, proposal_repo=proposal_repo)
    client = TestClient(app)

    response = client.get("/api/v1/components")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["group"] == "commerce"
    assert data[0]["description"] == "Cart, payments and order placement"
    # A component with no group is a legitimate state — the chip is omitted
    # by the frontend, never filled with a placeholder like "Uncategorized".
    assert data[1]["group"] is None
    assert data[1]["description"] is None


def test_components_module_five_file_shape():
    # AC4: the feature follows the five-file convention exactly.
    from pathlib import Path

    from src.api.v1 import components

    pkg_dir = Path(components.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }
