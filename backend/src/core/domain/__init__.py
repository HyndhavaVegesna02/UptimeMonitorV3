"""core.domain — pure data; depends on nothing."""

from src.core.domain.signal import Health, Provenance, SignalObservation
from src.core.domain.status import (
    ComponentStatus,
    IngestResult,
    StatusChange,
    STATUS_SEVERITY,
    severity_rank,
    is_worse,
)
from src.core.domain.verdict import Verdict
from src.core.domain.proposal import ProposalState, StatusProposal, is_valid_transition

__all__ = [
    "ComponentStatus",
    "Health",
    "IngestResult",
    "Provenance",
    "SignalObservation",
    "StatusChange",
    "Verdict",
    "ProposalState",
    "StatusProposal",
    "is_valid_transition",
    "STATUS_SEVERITY",
    "severity_rank",
    "is_worse",
]


