"""Tests for the publications API feature (STORY-037, Phase D — AC3; STORY-072 AC3).

GET /api/v1/publications → list of PublicationDTO, most-recent-first.
Empty repo → 200 + [].
Five-file shape test.
lint-imports 5 kept / 0 broken (publications added to api-feature-independence).
STORY-072: PublicationDTO carries `outcome` (succeeded/failed).
"""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from src.composition.app import create_app
from src.core.domain.publication import Publication, PublicationOutcome
from src.core.domain.status import ComponentStatus
from tests.fakes import FakeProposalRepository, FakePublicationRepository


def _utc(hour: int) -> datetime:
    return datetime(2026, 6, 29, hour, 0, 0, tzinfo=timezone.utc)


def test_get_publications_empty():
    """AC3: GET /api/v1/publications → 200 + [] when no publications exist."""
    pub_repo = FakePublicationRepository()
    app = create_app(
        proposal_repo=FakeProposalRepository(),
        publication_repo=pub_repo,
    )
    client = TestClient(app)

    response = client.get("/api/v1/publications")
    assert response.status_code == 200
    assert response.json() == []


def test_get_publications_most_recent_first():
    """AC3: GET /api/v1/publications returns publications ordered most-recent-first."""
    pub_repo = FakePublicationRepository()
    earlier = Publication(
        component_id="checkout",
        status=ComponentStatus.DEGRADED,
        published_at=_utc(10),
    )
    later = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=_utc(12),
    )
    pub_repo.record(earlier)
    pub_repo.record(later)

    app = create_app(
        proposal_repo=FakeProposalRepository(),
        publication_repo=pub_repo,
    )
    client = TestClient(app)

    response = client.get("/api/v1/publications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # most-recent-first
    assert data[0]["status"] == "operational"
    assert data[1]["status"] == "degraded"


def test_get_publications_dto_shape():
    """AC3/STORY-072 AC3: PublicationDTO has the expected fields (distinct from
    domain Publication), including `outcome`."""
    pub_repo = FakePublicationRepository()
    pub = Publication(
        component_id="login",
        status=ComponentStatus.MAJOR_OUTAGE,
        published_at=_utc(8),
        proposal_id=5,
        outcome=PublicationOutcome.FAILED,
    )
    saved = pub_repo.record(pub)

    app = create_app(
        proposal_repo=FakeProposalRepository(),
        publication_repo=pub_repo,
    )
    client = TestClient(app)

    response = client.get("/api/v1/publications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    item = data[0]
    assert item["component_id"] == "login"
    assert item["status"] == "major_outage"
    assert item["proposal_id"] == 5
    assert item["outcome"] == "failed"
    assert item["id"] == saved.id
    assert "published_at" in item


def test_get_publications_outcome_defaults_to_succeeded():
    """STORY-072 AC3: a Publication recorded without an explicit outcome
    (the historical/success-only shape) still round-trips as 'succeeded'."""
    pub_repo = FakePublicationRepository()
    pub = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=_utc(9),
    )
    pub_repo.record(pub)

    app = create_app(
        proposal_repo=FakeProposalRepository(),
        publication_repo=pub_repo,
    )
    client = TestClient(app)

    response = client.get("/api/v1/publications")
    assert response.status_code == 200
    data = response.json()
    assert data[0]["outcome"] == "succeeded"


def test_publications_module_five_file_shape():
    """AC3: The publications feature follows the five-file convention."""
    from pathlib import Path

    from src.api.v1 import publications

    pkg_dir = Path(publications.__file__).parent
    py_files = {p.name for p in pkg_dir.glob("*.py")}
    assert py_files == {
        "__init__.py",
        "controller.py",
        "models.py",
        "validation.py",
        "service.py",
    }


def test_get_publications_serializes_author():
    """STORY-066 AC3: GET /api/v1/publications serializes author (string | null)."""
    # 1. We construct a FakePublicationRepository with proposal_to_actor mapped
    pub_repo = FakePublicationRepository(proposal_to_actor={42: "Alice"})

    # 2. Record two publications: one with proposal_id=42 (author="Alice"), one with proposal_id=None (author=None)
    pub1 = Publication(
        component_id="checkout",
        status=ComponentStatus.DEGRADED,
        published_at=_utc(10),
        proposal_id=42,
    )
    pub2 = Publication(
        component_id="checkout",
        status=ComponentStatus.OPERATIONAL,
        published_at=_utc(12),
        proposal_id=None,
    )
    pub_repo.record(pub1)
    pub_repo.record(pub2)

    app = create_app(
        proposal_repo=FakeProposalRepository(),
        publication_repo=pub_repo,
    )
    client = TestClient(app)

    response = client.get("/api/v1/publications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Ordered by published_at DESC, so pub2 (hour 12) is first, pub1 (hour 10) is second.
    assert data[0]["proposal_id"] is None
    assert data[0]["author"] is None

    assert data[1]["proposal_id"] == 42
    assert data[1]["author"] == "Alice"
