from datetime import datetime, timezone

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.composition.publish_helper import RecordingPublisher, StatusWritebackPublisher
from src.core.domain.component import Component
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus
from tests.fakes import (
    FakeClock,
    FakeComponentRepository,
    FakeProposalRepository,
    FakePublicationRepository,
    RecordingStatusPublisher,
)


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
    assert event["action"] == "approved"


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
    from pathlib import Path

    from src.api.v1 import decisions
    from src.api.v1.decisions import models
    from src.core.domain.proposal import StatusProposal

    # AC1: the feature follows the five-file shape exactly.
    pkg_dir = Path(decisions.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }

    # AC1: DTO types are distinct from canonical domain types (no domain leak).
    assert models.DecisionRequest is not StatusProposal
    assert models.DecisionResponse is not StatusProposal


def test_decision_endpoint_lost_race_returns_409():
    """A concurrent double-submit (proposal resolved between get and resolve) maps
    to 409, not 500. The repository's resolve() raises ProposalNotOpenError when the
    row is no longer OPEN; the edge service maps that to 409."""
    from src.core.domain.proposal import ProposalNotOpenError

    class LostRaceRepo(FakeProposalRepository):
        # get() still reports the proposal OPEN (the request passed the guard),
        # but resolve() fails as a concurrent request already resolved it.
        def resolve(self, proposal_id, *, to_state, reason, resolved_at) -> None:
            raise ProposalNotOpenError(
                f"Proposal {proposal_id} not found or not in open state."
            )

    repo = LostRaceRepo()
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
    assert response.status_code == 409
    # No approval event recorded on the lost-race path.
    assert repo.approval_events == []


def test_decision_endpoint_approve_publishes_and_writes_back_status():
    """AC1/AC2: approving via HTTP publishes through the injected chain — a
    publication is recorded AND components.status is written back, visible via
    GET /api/v1/components. Composes the REAL StatusWritebackPublisher +
    RecordingPublisher chain with fakes standing in for the DB/Statuspage I/O
    edges (2026-06-29 composition-test agreement) and injects it through
    create_app's `publisher=` override."""
    proposal_repo = FakeProposalRepository()
    component_repo = FakeComponentRepository(
        components=[
            Component(
                id="checkout",
                name="Checkout",
                status=ComponentStatus.OPERATIONAL,
                app_id="app-1",
            )
        ]
    )
    publication_repo = FakePublicationRepository()
    clock = FakeClock(datetime(2026, 6, 28, 12, 0, 0, tzinfo=timezone.utc))
    statuspage_delegate = RecordingStatusPublisher()
    publisher = StatusWritebackPublisher(
        RecordingPublisher(statuspage_delegate, publication_repo, clock),
        component_repo,
    )

    app = create_app(
        proposal_repo=proposal_repo,
        component_repo=component_repo,
        publication_repo=publication_repo,
        clock=clock,
        publisher=publisher,
    )
    client = TestClient(app)

    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = proposal_repo.create_open(prop)
    assert saved is not None

    response = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "approve", "actor": "ops-1", "notes": "Approve it"},
    )
    assert response.status_code == 200

    # AC2: components.status is written back — GET /components serves it.
    comp_response = client.get("/api/v1/components")
    assert comp_response.status_code == 200
    assert comp_response.json() == [
        {"id": "checkout", "name": "Checkout", "status": "degraded"}
    ]

    # AC1: a publication was recorded (delegate publish succeeded).
    pubs = publication_repo.list_recent()
    assert len(pubs) == 1
    assert pubs[0].component_id == "checkout"
    assert pubs[0].status == ComponentStatus.DEGRADED

    # The Statuspage stand-in received the change too.
    assert len(statuspage_delegate.published) == 1
    assert statuspage_delegate.published[0].component_id == "checkout"
