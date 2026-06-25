"""core.domain — pure data; depends on nothing."""

from src.core.domain.signal import Health, Provenance, SignalObservation
from src.core.domain.status import ComponentStatus, IngestResult, StatusChange
from src.core.domain.verdict import Verdict

__all__ = [
    "ComponentStatus",
    "Health",
    "IngestResult",
    "Provenance",
    "SignalObservation",
    "StatusChange",
    "Verdict",
]
