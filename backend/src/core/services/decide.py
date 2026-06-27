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
        opened = self._proposal_repo.get_open(component_id)
        proposed_is_degradation = is_worse(proposed_status, current_status)
        proposed_is_better = severity_rank(proposed_status) < severity_rank(current_status)

        publish_change = None
        action = DecideAction.NOOP

        if proposed_is_better:
            publish_change = StatusChange(component_id=component_id, status=proposed_status)
            action = DecideAction.PUBLISHED_RECOVERY

        if proposed_is_degradation:
            if opened is None:
                prop = StatusProposal(
                    component_id=component_id,
                    from_status=current_status,
                    to_status=proposed_status,
                    state=ProposalState.OPEN,
                    proposed_at=now,
                )
                persisted = self._proposal_repo.create_open(prop)
                if persisted is None:
                    action = DecideAction.NOOP
                else:
                    action = DecideAction.PROPOSED
            elif opened.to_status != proposed_status:
                self._proposal_repo.resolve(
                    opened.id,
                    to_state=ProposalState.SUPERSEDED,
                    reason=reason,
                    resolved_at=now,
                )
                prop = StatusProposal(
                    component_id=component_id,
                    from_status=current_status,
                    to_status=proposed_status,
                    state=ProposalState.OPEN,
                    proposed_at=now,
                )
                persisted = self._proposal_repo.create_open(prop)
                if persisted is None:
                    action = DecideAction.NOOP
                else:
                    action = DecideAction.SUPERSEDED
            else:
                # open.to_status == proposed_status -> leave it
                action = DecideAction.NOOP
        else:
            # proposed is operational-or-equal vs published -> no human gate
            if opened is not None:
                self._proposal_repo.resolve(
                    opened.id,
                    to_state=ProposalState.OBSOLETED,
                    reason=reason,
                    resolved_at=now,
                )
                action = DecideAction.OBSOLETED

        if publish_change is not None:
            self._publisher.publish(publish_change)

        return action



