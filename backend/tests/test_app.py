from fastapi.testclient import TestClient
from src.composition.app import create_app
from tests.fakes import FakeProposalRepository


def test_health_endpoint():
    # Arrange
    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    client = TestClient(app)

    # Act
    response = client.get("/api/v1/health")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_lifespan_disposes_engine():
    from unittest.mock import MagicMock

    from fastapi.testclient import TestClient
    from src.composition.app import create_app
    from tests.fakes import FakeProposalRepository

    # Create mock engine
    mock_engine = MagicMock()

    repo = FakeProposalRepository()
    app = create_app(proposal_repo=repo)
    app.state.db_engine = mock_engine  # inject mock engine

    # Use TestClient as context manager to trigger startup and shutdown lifespan events
    with TestClient(app):
        # Startup triggered
        pass
    # Shutdown triggered

    # Verify that dispose was called
    mock_engine.dispose.assert_called_once()
