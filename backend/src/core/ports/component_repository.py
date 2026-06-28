"""The component repository port (dossier §9, §17) — persistence for components."""

from abc import ABC, abstractmethod

from src.core.domain.component import Component


class ComponentRepository(ABC):
    """Port interface for listing system components (dossier §9, §17)."""

    @abstractmethod
    def list_components(self) -> list[Component]:
        """Retrieve all components from the spine.

        Returns:
            list[Component]: A list of all components. Returns `[]` if none exist.
        """
        raise NotImplementedError
