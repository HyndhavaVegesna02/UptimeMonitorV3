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
