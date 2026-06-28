"""In-memory fakes for the core ports (STORY-005, AC2).

These live UNDER `tests/`, never in `src/adapters/`, so the production edge stays
clean and `adapters-independence` is untouched. Each fake implements exactly one
core port using only stdlib + canonical domain types — no Dynatrace, Statuspage,
Neon, DB, or network. They are the in-memory doubles every later zone's test can
inject in place of a real adapter.
"""

from collections.abc import Sequence
from datetime import datetime

from src.core.domain import Component, IngestResult, SignalObservation, StatusChange
from src.core.domain.proposal import (
    ProposalNotOpenError,
    ProposalState,
    StatusProposal,
)
from src.core.ports import (
    ClockPort,
    ComponentRepository,
    ObservationRepository,
    ProposalRepository,
    SignalIngestPort,
    StatusPublisherPort,
    WatermarkRepository,
)


class FakeClock(ClockPort):
    """A clock frozen at an injected instant, so tests control `now()`."""

    def __init__(self, fixed: datetime) -> None:
        self._fixed = fixed

    def now(self) -> datetime:
        return self._fixed


class FakeWatermarkRepository(WatermarkRepository):
    """An in-memory per-signal watermark store; `get` is None until advanced."""

    def __init__(self) -> None:
        self._marks: dict[str, datetime] = {}

    def get(self, signal_key: str) -> datetime | None:
        return self._marks.get(signal_key)

    def advance(self, signal_key: str, to: datetime) -> None:
        self._marks[signal_key] = to


class FakeObservationRepository(ObservationRepository):
    """An in-memory observation store that counts the rows it inserts."""

    def __init__(self) -> None:
        self.saved: list[SignalObservation] = []

    def save_new(self, batch: Sequence[SignalObservation]) -> int:
        self.saved.extend(batch)
        return len(batch)

    def in_window(
        self, signal_key: str, since: datetime, until: datetime
    ) -> Sequence[SignalObservation]:
        return [
            observation
            for observation in self.saved
            if observation.signal_key == signal_key
            and since <= observation.observed_at < until
        ]


class RecordingStatusPublisher(StatusPublisherPort):
    """A publisher that records every change instead of calling a real target."""

    def __init__(self) -> None:
        self.published: list[StatusChange] = []

    def publish(self, change: StatusChange) -> None:
        self.published.append(change)


class FakeSignalIngestPort(SignalIngestPort):
    """An ingest port that accepts the whole batch (no validation logic here).

    The real validate/dedupe/persist/advance pipeline is a Zone 2/core-services
    concern; this fake exists only to prove the interface is satisfiable and the
    signature speaks in canonical types.
    """

    def __init__(self) -> None:
        self.received: list[SignalObservation] = []

    def ingest_observations(self, batch: Sequence[SignalObservation]) -> IngestResult:
        self.received.extend(batch)
        return IngestResult(accepted=len(batch), rejected=0)


class FakeProposalRepository(ProposalRepository):
    """An in-memory dictionary-backed proposal repository for testing."""

    def __init__(self) -> None:
        self.proposals: dict[int, StatusProposal] = {}
        self.approval_events: list[dict] = []
        self._next_id: int = 1

    def create_open(self, proposal: StatusProposal) -> StatusProposal | None:
        # Check if an open proposal already exists for this component
        for existing in self.proposals.values():
            if (
                existing.component_id == proposal.component_id
                and existing.state == ProposalState.OPEN
            ):
                return None

        # Assign an ID and persist
        assigned_id = self._next_id
        self._next_id += 1
        persisted = proposal.model_copy(update={"id": assigned_id})
        self.proposals[assigned_id] = persisted
        return persisted

    def get_open(self, component_id: str) -> StatusProposal | None:
        for existing in self.proposals.values():
            if (
                existing.component_id == component_id
                and existing.state == ProposalState.OPEN
            ):
                return existing
        return None

    def resolve(
        self,
        proposal_id: int,
        *,
        to_state: ProposalState,
        reason: str | None,
        resolved_at: datetime,
    ) -> None:
        # Mirror PostgresProposalRepository.resolve: a missing or no-longer-OPEN
        # proposal cannot be resolved and raises ProposalNotOpenError (a single
        # conditional UPDATE in the real adapter cannot distinguish the two).
        existing = self.proposals.get(proposal_id)
        if existing is None or existing.state != ProposalState.OPEN:
            raise ProposalNotOpenError(
                f"Proposal {proposal_id} not found or not in open state."
            )
        updated = existing.model_copy(
            update={
                "state": to_state,
                "reason": reason,
                "resolved_at": resolved_at,
            }
        )
        self.proposals[proposal_id] = updated

    def record_approval_event(
        self,
        proposal_id: int,
        *,
        actor: str,
        action: str,
        notes: str | None,
        occurred_at: datetime,
    ) -> None:
        self.approval_events.append(
            {
                "proposal_id": proposal_id,
                "actor": actor,
                "action": action,
                "notes": notes,
                "occurred_at": occurred_at,
            }
        )

    def get(self, proposal_id: int) -> StatusProposal | None:
        return self.proposals.get(proposal_id)

    def list_open(self) -> list[StatusProposal]:
        return [p for p in self.proposals.values() if p.state == ProposalState.OPEN]


class FakeComponentRepository(ComponentRepository):
    """An in-memory component repository for testing."""

    def __init__(self, components: list[Component] | None = None) -> None:
        self._components = list(components) if components is not None else []

    def list_components(self) -> list[Component]:
        return self._components
