"""The component repository port (dossier §9, §17) — persistence for components.

STORY-016a (Sprint 17): adds `get(component_id) -> Component | None` for the
pipeline orchestrator (dossier §8 step 5) to read current_status per-component.
STORY-045: adds `set_status` — the write-back the approve and recovery publish
paths use to persist the newly-published status (dossier §12).
"""

from abc import ABC, abstractmethod

from src.core.domain.component import Component
from src.core.domain.status import ComponentStatus


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

    @abstractmethod
    def set_status(self, component_id: str, status: ComponentStatus) -> None:
        """Write back a component's published status (dossier §9, §12, §17, STORY-045).

        Called by the composition-layer `StatusWritebackPublisher` decorator
        (`composition/publish_helper.py`) right before the best-effort external
        publish — this is the durable write that makes `components.status`
        (and therefore `GET /api/v1/components` and the next `decide` cycle's
        `current_status`) reflect an approved degradation or an auto-published
        recovery.

        Raises `ComponentNotFoundError` (`core/domain/component.py`) when
        `component_id` does not exist — never a bare `ValueError`
        (2026-06-28 check-then-act agreement) and never a silent no-op: an
        unknown component id here means the topology seed and the change
        disagree, which must be loud. The fake and `DynamoComponentRepository`
        raise this identically (2026-06-26 fake/adapter parity agreement).
        """
        raise NotImplementedError
