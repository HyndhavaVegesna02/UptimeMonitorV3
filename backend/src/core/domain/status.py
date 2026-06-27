"""Canonical status vocabulary for the publish + ingest ports (dossier §6).

These are the vendor-neutral types the core's ports speak in. `ComponentStatus`
is a CLOSED enum of the states the core reasons about; the mapping from a status
to whatever string Statuspage expects lives ONLY in the Zone 5 adapter — this
module never mentions a vendor. A reader who has never heard of Statuspage must
understand every name here.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class ComponentStatus(str, Enum):
    """Closed set of canonical component states (dossier §6).

    The core decides one of these; the publish adapter translates it to the
    vendor's own string. Keeping the set closed means an unknown status can never
    leak through the port.
    """

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    PARTIAL_OUTAGE = "partial_outage"
    MAJOR_OUTAGE = "major_outage"


class StatusChange(BaseModel):
    """What the core asks the publisher to apply: a status for one component.

    `component_id` is the canonical component identifier the core owns — never a
    Statuspage id (dossier §6). The publish adapter is responsible for resolving
    it to the vendor's id and mapping `status` to the vendor's vocabulary.
    """

    model_config = ConfigDict(frozen=True)

    component_id: str
    """Canonical component id owned by the core; the adapter resolves the vendor id."""

    status: ComponentStatus
    """The canonical state to publish for this component."""


class IngestResult(BaseModel):
    """The outcome of ingesting one batch: how many were accepted vs rejected.

    Validation and quarantine happen on the core side of the ingest boundary
    (dossier §8); this is the canonical summary the port hands back. A rejected
    observation is one the core refused — it never silently disappears.
    """

    model_config = ConfigDict(frozen=True)

    accepted: int
    """Count of observations the core accepted and persisted."""

    rejected: int
    """Count of observations the core refused (quarantined as rejections)."""


STATUS_SEVERITY: dict[ComponentStatus, int] = {
    ComponentStatus.OPERATIONAL: 0,
    ComponentStatus.DEGRADED: 1,
    ComponentStatus.PARTIAL_OUTAGE: 2,
    ComponentStatus.MAJOR_OUTAGE: 3,
}


def severity_rank(status: ComponentStatus) -> int:
    """Returns the severity rank of a ComponentStatus."""
    return STATUS_SEVERITY[status]


def is_worse(a: ComponentStatus, b: ComponentStatus) -> bool:
    """Returns True if status 'a' is strictly worse than status 'b'."""
    return severity_rank(a) > severity_rank(b)

