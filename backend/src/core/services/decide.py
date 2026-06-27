from datetime import datetime
from enum import Enum

from src.core.domain import ComponentStatus, StatusChange, ProposalState, StatusProposal
from src.core.domain.status import is_worse, severity_rank
from src.core.ports import ProposalRepository, StatusPublisherPort


class DecideAction(str, Enum):
    NOOP = "noop"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    OBSOLETED = "obsoleted"
    PUBLISHED_RECOVERY = "published_recovery"


class DecideService:
    def __init__(
        self,
        *,
        proposal_repo: ProposalRepository,
        publisher: StatusPublisherPort,
    ) -> None:
        self._proposal_repo = proposal_repo
        self._publisher = publisher

    def decide(
        self,
        *,
        component_id: str,
        proposed_status: ComponentStatus,
        current_status: ComponentStatus,
        now: datetime,
        reason: str | None = None,
    ) -> DecideAction:
        return DecideAction.NOOP
