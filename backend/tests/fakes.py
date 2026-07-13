"""In-memory fakes for the core ports (STORY-005, AC2).

These live UNDER `tests/`, never in `src/adapters/`, so the production edge stays
clean and `adapters-independence` is untouched. Each fake implements exactly one
core port using only stdlib + canonical domain types — no Dynatrace, Statuspage,
Neon, DB, or network. They are the in-memory doubles every later zone's test can
inject in place of a real adapter.
"""

from collections.abc import Sequence
from datetime import datetime

from src.core.domain import (
    Component,
    ComponentStatus,
    IngestResult,
    MaintenanceWindow,
    Publication,
    Signal,
    SignalObservation,
    StatusChange,
)
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.maintenance import MaintenanceWindowNotFoundError
from src.core.domain.proposal import (
    ProposalNotOpenError,
    ProposalState,
    StatusProposal,
)
from src.core.ports import (
    ClockPort,
    ComponentRepository,
    MaintenanceRepository,
    ObservationRepository,
    ProposalRepository,
    PublicationRepository,
    SignalIngestPort,
    SignalRepository,
    StatusPublisherPort,
    WatermarkRepository,
)

# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)
from src.core.ports.sample_mode_repository import SampleModeRepository


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

    def get(self, component_id: str) -> Component | None:
        """Return the component with the given id, or None if not found.

        Parity with PostgresComponentRepository.get (2026-06-26 fake/adapter
        parity agreement): both return None on not-found, never raise.
        """
        for component in self._components:
            if component.id == component_id:
                return component
        return None

    def set_status(self, component_id: str, status: ComponentStatus) -> None:
        """Write back a component's status; raises ComponentNotFoundError if unknown.

        Parity with PostgresComponentRepository.set_status (2026-06-26
        fake/adapter parity agreement, STORY-045): both raise
        `ComponentNotFoundError` on an unknown id, never a bare `ValueError`.
        """
        for index, component in enumerate(self._components):
            if component.id == component_id:
                self._components[index] = component.model_copy(
                    update={"status": status}
                )
                return
        raise ComponentNotFoundError(f"Component {component_id!r} not found.")


class FakePublicationRepository(PublicationRepository):
    """An in-memory publication repository for testing (STORY-037).

    Fake/adapter parity (2026-06-26): empty → []; record returns a persisted
    Publication with an id; list_recent returns most-recent-first.
    """

    def __init__(self) -> None:
        self._publications: dict[int, Publication] = {}
        self._next_id: int = 1

    def record(self, publication: Publication) -> Publication:
        """Persist a publication and return it with an assigned id."""
        pub_id = self._next_id
        self._next_id += 1
        saved = publication.model_copy(update={"id": pub_id})
        self._publications[pub_id] = saved
        return saved

    def list_recent(self, limit: int = 50) -> list[Publication]:
        """Return up to `limit` publications ordered most-recent-first."""
        pubs = sorted(
            self._publications.values(),
            key=lambda p: p.published_at,
            reverse=True,
        )
        return pubs[:limit]


class FakeSignalRepository(SignalRepository):
    """An in-memory seeded-topology signal repository for testing (STORY-044).

    Parity with `PostgresSignalRepository` (2026-06-26 fake/adapter parity
    agreement): `list_signals` returns `[]` when empty and is ordered by
    `signal_key`; `get` returns `None` on an unknown key, never raises.
    """

    def __init__(self, signals: list[Signal] | None = None) -> None:
        self._signals = list(signals) if signals is not None else []

    def list_signals(self) -> list[Signal]:
        return sorted(self._signals, key=lambda s: s.signal_key)

    def get(self, signal_key: str) -> Signal | None:
        for signal in self._signals:
            if signal.signal_key == signal_key:
                return signal
        return None


class FakeSampleModeRepository(SampleModeRepository):
    """An in-memory sample-mode flag store for testing (STORY-048 D2).

    TEMPORARY feature — see docs/scrum/wiki/sample-mode.md. Parity with
    `PostgresSampleModeRepository` (2026-06-26 fake/adapter parity
    agreement): never-set -> False; idempotent re-set; never raises.

    Accepts an optional shared `store` dict so a test can prove persistence
    across a FRESH repository instance (mirroring how two `PostgresSampleModeRepository`
    instances share state via the same `Engine`/database) — the default `None`
    gives each instance its own private dict, matching every other fake's
    normal per-instance-only behavior.
    """

    def __init__(self, store: dict[str, bool] | None = None) -> None:
        self._store: dict[str, bool] = store if store is not None else {}

    def is_enabled(self) -> bool:
        return self._store.get("enabled", False)

    def set_enabled(self, enabled: bool) -> None:
        self._store["enabled"] = enabled


class FakeMaintenanceRepository(MaintenanceRepository):
    """An in-memory maintenance repository for testing."""

    def __init__(self, windows: list[MaintenanceWindow] | None = None) -> None:
        self._windows = {}
        self._next_id = 1
        if windows is not None:
            for w in windows:
                w_id = w.id if w.id is not None else self._next_id
                if w.id is None:
                    self._next_id += 1
                self._windows[w_id] = w.model_copy(update={"id": w_id})

    def list_windows(self) -> list[MaintenanceWindow]:
        """Retrieve all scheduled maintenance windows ordered by starts_at."""
        return sorted(self._windows.values(), key=lambda w: w.starts_at)

    def create(self, window: MaintenanceWindow) -> MaintenanceWindow:
        """Persist a new maintenance window."""
        w_id = window.id if window.id is not None else self._next_id
        if window.id is None:
            self._next_id += 1
        saved = window.model_copy(update={"id": w_id})
        self._windows[w_id] = saved
        return saved

    def is_under_maintenance(self, component_id: str, at: datetime) -> bool:
        """Check if a component is under active maintenance at a given timestamp."""
        for w in self._windows.values():
            if w.component_id == component_id:
                if w.starts_at <= at < w.ends_at:
                    return True
        return False

    def delete(self, window_id: int) -> None:
        """Delete a maintenance window by its ID."""
        if window_id not in self._windows:
            raise MaintenanceWindowNotFoundError(
                f"Maintenance window with ID {window_id} not found."
            )
        del self._windows[window_id]

