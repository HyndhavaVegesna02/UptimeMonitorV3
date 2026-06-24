"""The canonical signal vocabulary (dossier §5).

`SignalObservation` is the spine of the system: the flattened, vendor-neutral
form of one synthetic monitor execution from one location. Vendor identifiers
live ONLY inside `Provenance`; every other field reads to someone who has never
heard of Dynatrace (vocabulary rule P3, dossier §6).
"""

from enum import Enum


class Health(str, Enum):
    """Closed health verdict for one observation.

    Not pass/fail — `degraded` lets a partial outage be expressed (dossier §5).
    """

    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
