from datetime import datetime, timezone

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus
from tests.fakes import FakeProposalRepository


def test_decision_endpoint_validation_error():
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    # Missing actor
    response = client.post(
        "/api/v1/decisions/1",
        json={"action": "approve", "notes": "looks good"},
    )
    assert response.status_code == 422

    # Empty actor
    response = client.post(
        "/api/v1/decisions/1",
        json={"action": "approve", "actor": "", "notes": "looks good"},
    )
    assert response.status_code == 422

    # Invalid action
    response = client.post(
        "/api/v1/decisions/1",
        json={"action": "invalid_action", "actor": "ops-1"},
    )
    assert response.status_code == 422


def test_decision_endpoint_approve_success():
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    response = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "approve", "actor": "ops-1", "notes": "Approve it"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"] == saved.id
    assert data["state"] == "approved"
    assert "resolved_at" in data

    # Verify state in repo
    updated = repo.get(saved.id)
    assert updated is not None
    assert updated.state == ProposalState.APPROVED
    assert updated.reason == "Approve it"

    # Verify event recorded
    assert len(repo.approval_events) == 1
    event = repo.approval_events[0]
    assert event["proposal_id"] == saved.id
    assert event["actor"] == "ops-1"
    assert event["action"] == "approve"


def test_decision_endpoint_reject_success():
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    response = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "reject", "actor": "ops-1", "notes": "Reject it"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["proposal_id"] == saved.id
    assert data["state"] == "rejected"

    updated = repo.get(saved.id)
    assert updated is not None
    assert updated.state == ProposalState.REJECTED


def test_decision_endpoint_proposal_not_found():
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    response = client.post(
        "/api/v1/decisions/999",
        json={"action": "approve", "actor": "ops-1"},
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_decision_endpoint_proposal_already_terminal_conflict():
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    # First approve succeeds
    response1 = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "approve", "actor": "ops-1"},
    )
    assert response1.status_code == 200

    # Second approve fails with 409
    response2 = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "approve", "actor": "ops-2"},
    )
    assert response2.status_code == 409
    assert "cannot transition" in response2.json()["detail"].lower()


def test_decision_endpoint_commit_first_pure_repo_commit():
    """Assert that the decision endpoint returns success purely from the repository commit

    (i.e. no publisher or third-party dependencies are wired to block or fail it).
    """
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = repo.create_open(prop)
    assert saved is not None

    response = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "approve", "actor": "ops-1"},
    )

    # Returns 200 cleanly purely on repo resolution commit
    assert response.status_code == 200
    assert response.json()["proposal_id"] == saved.id
    assert response.json()["state"] == "approved"


def test_decisions_module_structure_and_dto_distinction():
    from src.api.v1.decisions import models
    from src.core.domain.proposal import StatusProposal

    # Assert that DTO types are different from domain types
    assert models.DecisionRequest is not StatusProposal
    assert models.DecisionResponse is not StatusProposal
