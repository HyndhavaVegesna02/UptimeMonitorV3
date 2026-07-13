"""The maintenance repository port (dossier §9, §10, §17)."""

from abc import ABC, abstractmethod
from datetime import datetime

from src.core.domain.maintenance import MaintenanceWindow


class MaintenanceRepository(ABC):
    """Port interface for storing and querying maintenance windows (dossier §9, §10, §17)."""

    @abstractmethod
    def list_windows(self) -> list[MaintenanceWindow]:
        """Retrieve all scheduled maintenance windows.

        Returns:
            list[MaintenanceWindow]: Scheduled windows ordered by starts_at.
                Returns `[]` if none exist.
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, window: MaintenanceWindow) -> MaintenanceWindow:
        """Persist a new maintenance window.

        Args:
            window: The MaintenanceWindow to save.

        Returns:
            MaintenanceWindow: The saved window with its ID populated.
        """
        raise NotImplementedError

    @abstractmethod
    def is_under_maintenance(self, component_id: str, at: datetime) -> bool:
        """Check if a component is under active maintenance at a given timestamp.

        The check uses inclusive start / exclusive end boundaries: starts_at <= at < ends_at.

        Args:
            component_id: The ID of the component.
            at: The query timestamp (tz-aware UTC).

        Returns:
            bool: True if the component is under maintenance, False otherwise.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, window_id: int) -> None:
        """Delete a maintenance window by its ID.

        Args:
            window_id: The ID of the maintenance window to delete.

        Raises:
            MaintenanceWindowNotFoundError: If the window ID does not exist.
        """
        raise NotImplementedError
