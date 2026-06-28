"""Controller for components (api/v1/components feature).

Cites dossier §13, §17.
"""

from fastapi import APIRouter, Depends

from src.api.v1.components.models import ComponentDTO
from src.api.v1.components.service import (
    ComponentsService,
    get_components_service,
)

router = APIRouter()


@router.get("/components", response_model=list[ComponentDTO])
def list_components(
    service: ComponentsService = Depends(get_components_service),
) -> list[ComponentDTO]:
    """Retrieve all components and their statuses."""
    return service.get_all_components()
