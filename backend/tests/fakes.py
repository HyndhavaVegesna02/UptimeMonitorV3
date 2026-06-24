"""In-memory fakes for the core ports (STORY-005, AC2).

These live UNDER `tests/`, never in `src/adapters/`, so the production edge stays
clean and `adapters-independence` is untouched. Each fake implements exactly one
core port using only stdlib + canonical domain types — no Dynatrace, Statuspage,
Neon, DB, or network. They are the in-memory doubles every later zone's test can
inject in place of a real adapter.
"""

from collections.abc import Sequence
from datetime import datetime

from src.core.domain import IngestResult, SignalObservation, StatusChange
from src.core.ports import (
    ClockPort,
    ObservationRepository,
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

    def ingest_observations(
        self, batch: Sequence[SignalObservation]
    ) -> IngestResult:
        self.received.extend(batch)
        return IngestResult(accepted=len(batch), rejected=0)
