from fastapi.testclient import TestClient
from src.composition.app import create_app
from tests.fakes import (
    FakeComponentRepository,
    FakeProposalRepository,
    FakePublicationRepository,
)


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


def test_create_app_component_repo_without_publication_repo_still_writes_back():
    """STORY-047 AC1: a component_repo injected without a publication_repo
    yields StatusWritebackPublisher(LoggingPublisher()) — write-back still
    applies — never a bare LoggingPublisher that silently skips it."""
    from src.composition.publish_helper import (
        LoggingPublisher,
        StatusWritebackPublisher,
    )

    proposal_repo = FakeProposalRepository()
    component_repo = FakeComponentRepository()
    app = create_app(proposal_repo=proposal_repo, component_repo=component_repo)

    assert isinstance(app.state.publisher, StatusWritebackPublisher)
    assert app.state.publisher._component_repo is component_repo
    assert isinstance(app.state.publisher._delegate, LoggingPublisher)


def test_create_app_publication_repo_without_component_repo_is_bare_logging():
    """STORY-047 AC1: without a component_repo there is nothing to write back
    to, so the fallback stays a bare LoggingPublisher regardless of whether a
    publication_repo was injected."""
    from src.composition.publish_helper import LoggingPublisher

    proposal_repo = FakeProposalRepository()
    publication_repo = FakePublicationRepository()
    app = create_app(proposal_repo=proposal_repo, publication_repo=publication_repo)

    assert type(app.state.publisher) is LoggingPublisher


def test_create_app_neither_repo_is_bare_logging():
    """STORY-047 AC1: with neither repo injected, the fallback is unchanged —
    a bare LoggingPublisher."""
    from src.composition.publish_helper import LoggingPublisher

    proposal_repo = FakeProposalRepository()
    app = create_app(proposal_repo=proposal_repo)

    assert type(app.state.publisher) is LoggingPublisher
