"""The component repository port (dossier §9, §17) — persistence for components.

STORY-016a (Sprint 17): adds `get(component_id) -> Component | None` for the
pipeline orchestrator (dossier §8 step 5) to read current_status per-component.
"""

from abc import ABC, abstractmethod

from src.core.domain.component import Component


class ComponentRepository(ABC):
    """Port interface for listing and looking up system components (dossier §9, §17)."""

    @abstractmethod
    def list_components(self) -> list[Component]:
        """Retrieve all components from the spine.

        Returns:
            list[Component]: A list of all components. Returns `[]` if none exist.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, component_id: str) -> Component | None:
        """Retrieve a single component by id (dossier §9, §17).

        Returns `None` when no component with `component_id` exists — never
        raises, never returns a sentinel value (fake/adapter parity
        agreement 2026-06-26). The pipeline orchestrator (dossier §8 step 5)
        uses this to read `current_status` before calling `DecideService.decide`.
        """
        raise NotImplementedError
