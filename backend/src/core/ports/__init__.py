"""core.ports — interfaces the core owns, expressed in domain types.

These ABCs are the inversion that lets the core depend on nothing: the core
declares the interfaces it needs (inbound ingest, outbound publish, persistence,
clock) and adapters in the outer zones implement them. Every signature reads in
canonical vocabulary only — a reader who has never heard of Dynatrace, Statuspage,
or Neon must understand it (dossier §6).
"""

from src.core.ports.clock import ClockPort
from src.core.ports.component_repository import ComponentRepository
from src.core.ports.observation_repository import ObservationRepository
from src.core.ports.proposal_repository import ProposalRepository
from src.core.ports.rejected_observation_repository import (
    RejectedObservationRepository,
)
from src.core.ports.signal_ingest import SignalIngestPort
from src.core.ports.status_publisher import StatusPublisherPort
from src.core.ports.watermark import WatermarkRepository

__all__ = [
    "ClockPort",
    "ObservationRepository",
    "RejectedObservationRepository",
    "SignalIngestPort",
    "StatusPublisherPort",
    "WatermarkRepository",
    "ProposalRepository",
    "ComponentRepository",
]
