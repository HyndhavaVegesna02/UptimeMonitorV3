"""Tests for the centralized error registry (_shared/errors.py).

Cites: Proposal (2026-07-10) §3.4 G2/G5, §6.2, §10 Phase 2.
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain import Signal
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.proposal import ProposalState, StatusProposal
from src.core.domain.status import ComponentStatus
from src.core.domain.topology import (
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)
from tests.fakes import (
    FakeComponentRepository,
    FakeProposalRepository,
    FakeSignalRepository,
)


def test_shared_errors_value_error_422(migrated_db) -> None:
    """Verify that ValueError (from invalid dates/times) maps to HTTP 422.

    Cites: Proposal (2026-07-10) §3.4 G2, §10 Phase 2.
    """
    app = create_app()
    client = TestClient(app)

    # In maintenance window creation, if ends_at <= starts_at, it raises ValueError
    # which should map to 422.
    response = client.post(
        "/api/v1/maintenance",
        json={
            "component_id": "checkout",
            "starts_at": "2026-06-28T12:00:00Z",
            "ends_at": "2026-06-28T11:00:00Z",  # End before start!
            "reason": "Upgrade",
        },
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_shared_errors_signal_not_found_404(migrated_db) -> None:
    """Verify that SignalNotFoundError maps to HTTP 404.

    Cites: Proposal (2026-07-10) §3.4 G2, §10 Phase 2.
    """
    signal_repo = FakeSignalRepository()  # Empty
    app = create_app(signal_repo=signal_repo)
    client = TestClient(app)

    response = client.get("/api/v1/availability?signal_key=nonexistent")
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Signal 'nonexistent' not found in the seeded topology."
    }


def test_shared_errors_signal_interval_unconfigured_409(migrated_db) -> None:
    """Verify that SignalIntervalUnconfiguredError maps to HTTP 409.

    Cites: Proposal (2026-07-10) §3.4 G2, §10 Phase 2.
    """
    signal = Signal(
        signal_key="checkout-http",
        name="Checkout HTTP",
        component_id="checkout",
        interval_seconds=None,
    )
    signal_repo = FakeSignalRepository(signals=[signal])
    app = create_app(signal_repo=signal_repo)
    client = TestClient(app)

    response = client.get("/api/v1/availability?signal_key=checkout-http")
    assert response.status_code == 409
    assert response.json() == {
        "detail": "Signal 'checkout-http' has no configured interval_seconds."
    }


def test_shared_errors_component_not_found_404(migrated_db) -> None:
    """Verify that ComponentNotFoundError maps to HTTP 404.

    Cites: Proposal (2026-07-10) §3.4 G2, §10 Phase 2.
    """
    component_repo = FakeComponentRepository()  # Empty
    app = create_app(component_repo=component_repo)
    client = TestClient(app)

    response = client.get("/api/v1/availability/component/nonexistent")
    assert response.status_code == 404
    assert response.json() == {"detail": "Component 'nonexistent' not found."}


def test_shared_errors_proposal_not_found_404(migrated_db) -> None:
    """Verify that ProposalNotFoundError maps to HTTP 404.

    Cites: Proposal (2026-07-10) §3.4 G2, §10 Phase 2.
    """
    proposal_repo = FakeProposalRepository()  # Empty
    app = create_app(proposal_repo=proposal_repo)
    client = TestClient(app)

    response = client.post(
        "/api/v1/decisions/999",
        json={"action": "approve", "actor": "ops-1"},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_shared_errors_proposal_not_open_409(migrated_db) -> None:
    """Verify that ProposalNotOpenError maps to HTTP 409.

    Cites: Proposal (2026-07-10) §3.4 G2, §10 Phase 2.
    """
    proposal_repo = FakeProposalRepository()
    prop = StatusProposal(
        component_id="checkout",
        from_status=ComponentStatus.OPERATIONAL,
        to_status=ComponentStatus.DEGRADED,
        state=ProposalState.OPEN,
        proposed_at=datetime(2026, 6, 28, 11, 0, 0, tzinfo=timezone.utc),
    )
    saved = proposal_repo.create_open(prop)
    # Force it into APPROVED state in the repository dictionary
    proposal_repo.proposals[saved.id] = saved.model_copy(
        update={
            "state": ProposalState.APPROVED,
            "resolved_at": datetime(2026, 6, 28, 11, 5, 0, tzinfo=timezone.utc),
        }
    )

    app = create_app(proposal_repo=proposal_repo)
    client = TestClient(app)

    response = client.post(
        f"/api/v1/decisions/{saved.id}",
        json={"action": "approve", "actor": "ops-1"},
    )
    assert response.status_code == 409
    assert "cannot transition" in response.json()["detail"].lower()


def test_shared_errors_unregistered_propagates(migrated_db) -> None:
    """Verify that an unregistered exception propagates normally and is not swallowed.

    Cites: Proposal (2026-07-10) §10 Phase 2.
    """
    app = create_app()

    @app.get("/test-unregistered-exception-propagation")
    def trigger_error() -> None:
        raise RuntimeError("Unregistered error that should propagate")

    client = TestClient(app, raise_server_exceptions=True)
    with pytest.raises(RuntimeError) as exc_info:
        client.get("/test-unregistered-exception-propagation")
    assert "Unregistered error that should propagate" in str(exc_info.value)
