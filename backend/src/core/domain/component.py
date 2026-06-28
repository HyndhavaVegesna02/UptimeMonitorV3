"""The component domain read type (dossier §9, §17).

Represents a system component with its displayed status.
"""

from pydantic import BaseModel, ConfigDict

from src.core.domain.status import ComponentStatus


class Component(BaseModel):
    """A system component with its display status (dossier §9, §17).

    Acts as a vendor-neutral read model representing the components table.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    status: ComponentStatus
    app_id: str
