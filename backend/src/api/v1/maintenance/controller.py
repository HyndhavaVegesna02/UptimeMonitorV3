"""Controller for scheduled maintenance (api/v1/maintenance feature).

Cites dossier §13, §10, §17.
"""

from fastapi import APIRouter, Depends

from src.api.v1.maintenance.models import (
    CreateMaintenanceRequest,
    MaintenanceWindowDTO,
)
from src.api.v1.maintenance.service import (
    MaintenanceService,
    get_maintenance_service,
)

router = APIRouter()


@router.get("/maintenance", response_model=list[MaintenanceWindowDTO])
def list_maintenance_windows(
    service: MaintenanceService = Depends(get_maintenance_service),
) -> list[MaintenanceWindowDTO]:
    """Retrieve all scheduled maintenance windows."""
    return service.list_windows()


@router.post("/maintenance", response_model=MaintenanceWindowDTO, status_code=201)
def schedule_maintenance_window(
    request: CreateMaintenanceRequest,
    service: MaintenanceService = Depends(get_maintenance_service),
) -> MaintenanceWindowDTO:
    """Schedule a new maintenance window."""
    return service.create_window(request)
