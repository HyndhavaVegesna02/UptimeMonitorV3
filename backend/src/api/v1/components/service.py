"""Service layer for components (api/v1/components feature).

Cites dossier §13, §17.
"""

from fastapi import Depends

from src.api.dependencies import get_component_repo
from src.api.v1.components.models import ComponentDTO
from src.core.ports import ComponentRepository


class ComponentsService:
    """Service handling retrieval and formatting of components."""

    def __init__(self, component_repo: ComponentRepository) -> None:
        self._component_repo = component_repo

    def get_all_components(self) -> list[ComponentDTO]:
        """Fetch all components from port and map them to DTOs.

        UNCONDITIONAL passthrough (STORY-226 AC4) — ``group``/``description``
        are copied verbatim from the repository entity, with no normalization
        performed here or in ``ComponentDTO``. This layer therefore inherits
        whatever ``load_config`` produced: ``description`` can never be ``""``
        at this seam because ``ComponentConfig``'s field validator normalizes
        a blank ``description`` to ``None`` at load (STORY-226 AC3) — the
        guarantee is made once, at the load boundary, not re-checked here.
        """
        components = self._component_repo.list_components()
        return [
            ComponentDTO(
                id=c.id,
                name=c.name,
                status=c.status.value,
                group=c.group,
                description=c.description,
            )
            for c in components
        ]


def get_components_service(
    component_repo: ComponentRepository = Depends(get_component_repo),
) -> ComponentsService:
    """Dependency provider for ComponentsService."""
    return ComponentsService(component_repo)
