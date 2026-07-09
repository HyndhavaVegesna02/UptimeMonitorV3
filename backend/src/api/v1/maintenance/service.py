"""Thin edge service for maintenance (api/v1/maintenance feature).

Cites dossier §13, §10, §17: the edge service validates HTTP input,
delegates to the core repository, and shapes the HTTP DTO response.
"""

from fastapi import Depends

from src.api.dependencies import get_maintenance_repo
from src.api.v1.maintenance.models import (
    CreateMaintenanceRequest,
    MaintenanceWindowDTO,
)
from src.api.v1.maintenance.validation import (
    validate_maintenance_request,
)
from src.core.domain.maintenance import MaintenanceWindow
from src.core.ports import MaintenanceRepository


class MaintenanceService:
    """Thin edge service handling maintenance scheduling and retrieval."""

    def __init__(self, maintenance_repo: MaintenanceRepository) -> None:
        self._maintenance_repo = maintenance_repo

    def list_windows(self) -> list[MaintenanceWindowDTO]:
        """Fetch all maintenance windows and map to DTOs."""
        windows = self._maintenance_repo.list_windows()
        return [
            MaintenanceWindowDTO(
                id=w.id,
                component_id=w.component_id,
                starts_at=w.starts_at,
                ends_at=w.ends_at,
                reason=w.reason,
            )
            for w in windows
        ]

    def create_window(self, request: CreateMaintenanceRequest) -> MaintenanceWindowDTO:
        """Validate, construct domain model, and persist the maintenance window."""
        # 1. Syntactic validation
        validate_maintenance_request(
            component_id=request.component_id,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
        )

        # 2. Domain model construction (enforces invariant)
        window = MaintenanceWindow(
            component_id=request.component_id,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            reason=request.reason,
        )

        # 3. Persist and return DTO
        saved = self._maintenance_repo.create(window)
        return MaintenanceWindowDTO(
            id=saved.id,
            component_id=saved.component_id,
            starts_at=saved.starts_at,
            ends_at=saved.ends_at,
            reason=saved.reason,
        )


def get_maintenance_service(
    maintenance_repo: MaintenanceRepository = Depends(get_maintenance_repo),
) -> MaintenanceService:
    """Dependency provider for MaintenanceService."""
    return MaintenanceService(maintenance_repo)
