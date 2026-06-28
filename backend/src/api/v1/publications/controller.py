"""Controller for the publications read endpoint (api/v1/publications feature).

Cites dossier §9, §12/T1.1, §17.
"""

from fastapi import APIRouter, Depends

from src.api.v1.publications.models import PublicationDTO
from src.api.v1.publications.service import (
    PublicationsService,
    get_publications_service,
)

router = APIRouter()


@router.get("/publications", response_model=list[PublicationDTO])
def list_publications(
    service: PublicationsService = Depends(get_publications_service),
) -> list[PublicationDTO]:
    """Retrieve recent publications most-recent-first (dossier §17 Publications tab)."""
    return service.list_recent()
