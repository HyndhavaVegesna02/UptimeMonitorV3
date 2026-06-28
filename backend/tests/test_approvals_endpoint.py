from datetime import datetime, timezone

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus
from tests.fakes import FakeComponentRepository, FakeProposalRepository


def test_get_approvals_empty():
    proposal_repo = FakeProposalRepository()
    component_repo = FakeComponentRepository()
    app = create_app(proposal_repo=proposal_repo, component_repo=component_repo)
    client = TestClient(app)

    response = client.get("/api/v1/approvals")
    assert response.status_code == 200
    assert response.json() == []


def test_get_approvals_mix_open_and_terminal():
    proposal_repo = FakeProposalRepository()
    component_repo = FakeComponentRepository()

    # Open proposal
    prop_open = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc),
    )
    saved_open = proposal_repo.create_open(prop_open)
    assert saved_open is not None

    # Terminal proposal (created open, then resolved to APPROVED)
    prop_terminal = StatusProposal(
        component_id="checkout-terminal",
        from_status=ComponentStatus.DEGRADED,
        to_status=ComponentStatus.OPERATIONAL,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved_terminal = proposal_repo.create_open(prop_terminal)
    assert saved_terminal is not None
    proposal_repo.resolve(
        saved_terminal.id,
        to_state=ProposalState.APPROVED,
        reason="looks good",
        resolved_at=datetime(2026, 6, 28, 11, 5, 0, tzinfo=timezone.utc),
    )

    app = create_app(proposal_repo=proposal_repo, component_repo=component_repo)
    client = TestClient(app)

    response = client.get("/api/v1/approvals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == saved_open.id
    assert data[0]["component_id"] == "checkout"
    assert data[0]["from_status"] == "operational"
    assert data[0]["to_status"] == "degraded"
    assert data[0]["state"] == "open"
    assert data[0]["proposed_at"].replace("+00:00", "Z") == "2026-06-28T12:00:00Z"


def test_get_approvals_multiple_open():
    # AC2: multiple open proposals (across components) are all returned.
    proposal_repo = FakeProposalRepository()
    component_repo = FakeComponentRepository()

    prop_a = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc),
    )
    prop_b = StatusProposal(
        component_id="catalogue",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 12, 30, 0, tzinfo=timezone.utc),
    )
    saved_a = proposal_repo.create_open(prop_a)
    saved_b = proposal_repo.create_open(prop_b)
    assert saved_a is not None and saved_b is not None

    app = create_app(proposal_repo=proposal_repo, component_repo=component_repo)
    client = TestClient(app)

    response = client.get("/api/v1/approvals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {row["id"] for row in data} == {saved_a.id, saved_b.id}


def test_approvals_module_five_file_shape():
    # AC4: the feature follows the five-file convention exactly.
    from pathlib import Path

    from src.api.v1 import approvals

    pkg_dir = Path(approvals.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }
