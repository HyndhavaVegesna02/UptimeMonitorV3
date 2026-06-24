"""The canonical signal vocabulary (dossier §5).

`SignalObservation` is the spine of the system: the flattened, vendor-neutral
form of one synthetic monitor execution from one location. Vendor identifiers
live ONLY inside `Provenance`; every other field reads to someone who has never
heard of Dynatrace (vocabulary rule P3, dossier §6).
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict


class Health(str, Enum):
    """Closed health verdict for one observation.

    Not pass/fail — `degraded` lets a partial outage be expressed (dossier §5).
    """

    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class Provenance(BaseModel):
    """Where an observation came from — the ONLY home for vendor identifiers.

    The core never reads these for logic; they exist for audit and traceability.
    `native_id` and `native_kind` are the vendor's own id and monitor type
    (e.g. http / clickpath / browser / nam), quarantined here so the rest of the
    canonical shape stays vendor-neutral (dossier §5, §6).
    """

    model_config = ConfigDict(frozen=True)

    system: str
    native_id: str
    native_kind: str
