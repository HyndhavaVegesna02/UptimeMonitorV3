"""Thin edge service for publications (api/v1/publications feature).

Cites dossier §9, §12/T1.1, §17: the edge service resolves the
PublicationRepository, calls list_recent, and shapes the PublicationDTO response.
The GET endpoint is a pure read; no mutation (TOCTOU N/A).
"""

from fastapi import Depends

from src.api.dependencies import get_publication_repo
from src.api.v1.publications.models import PublicationDTO
from src.core.ports.publication_repository import PublicationRepository


class PublicationsService:
    """Thin edge service that resolves and shapes publication DTOs."""

    def __init__(self, publication_repo: PublicationRepository) -> None:
        self._publication_repo = publication_repo

    def list_recent(self) -> list[PublicationDTO]:
        """Fetch recent publications and map to DTOs (most-recent-first)."""
        pubs = self._publication_repo.list_recent()
        return [
            PublicationDTO(
                id=p.id,
                component_id=p.component_id,
                status=p.status.value,
                published_at=p.published_at,
                proposal_id=p.proposal_id,
            )
            for p in pubs
        ]


def get_publications_service(
    publication_repo: PublicationRepository = Depends(get_publication_repo),
) -> PublicationsService:
    """Dependency provider for PublicationsService."""
    return PublicationsService(publication_repo)
