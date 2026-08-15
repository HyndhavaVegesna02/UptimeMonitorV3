"""The component domain read type (dossier §9, §17).

Represents a system component with its displayed status.
"""

from pydantic import BaseModel, ConfigDict

from src.core.domain.status import ComponentStatus


class ComponentNotFoundError(ValueError):
    """Raised when a component cannot be found by its id (dossier §9, §17).

    Mirrors `core/domain/proposal.py::ProposalNotFoundError`. Raised by
    `ComponentRepository.set_status` when the conditional write affects zero
    rows (2026-06-28 check-then-act agreement: never a bare `ValueError`) —
    both the fake and `DynamoComponentRepository` raise this identically
    (2026-06-26 fake/adapter parity agreement).
    """


class Component(BaseModel):
    """A system component with its display status (dossier §9, §17).

    Acts as a vendor-neutral read model representing the components table.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    status: ComponentStatus
    app_id: str
    group: str | None = None
    """Optional display sub-label (STORY-147) — decorative only, sourced from
    ``ComponentConfig.group`` via topology seeding; ``None`` is a legitimate
    state (a component not yet categorized)."""
    description: str | None = None
    """Optional one-line operator-facing description (STORY-147), sourced from
    ``ComponentConfig.description`` via topology seeding; ``None`` is a
    legitimate state, never a placeholder like ``"Uncategorized"``."""
