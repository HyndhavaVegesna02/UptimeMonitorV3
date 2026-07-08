"""core.domain — pure data; depends on nothing."""

from src.core.domain.component import Component
from src.core.domain.maintenance import MaintenanceWindow
from src.core.domain.proposal import ProposalState, StatusProposal, is_valid_transition
from src.core.domain.publication import Publication, PublicationOutcome
from src.core.domain.signal import Health, Provenance, SignalObservation
from src.core.domain.status import (
    STATUS_SEVERITY,
    ComponentStatus,
    IngestResult,
    StatusChange,
    is_worse,
    severity_rank,
)
from src.core.domain.topology import (
    Signal,
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)
from src.core.domain.verdict import Verdict

__all__ = [
    "ComponentStatus",
    "Health",
    "IngestResult",
    "Provenance",
    "Publication",
    "PublicationOutcome",
    "SignalObservation",
    "StatusChange",
    "Verdict",
    "ProposalState",
    "StatusProposal",
    "is_valid_transition",
    "STATUS_SEVERITY",
    "severity_rank",
    "is_worse",
    "Component",
    "MaintenanceWindow",
    "Signal",
    "SignalNotFoundError",
    "SignalIntervalUnconfiguredError",
]
