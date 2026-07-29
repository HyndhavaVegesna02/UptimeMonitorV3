"""The observation repository port (dossier §6, §8) — durable, deduplicated store.

`save_new` persists a batch of canonical observations, skipping any whose
idempotency key (`source_event_id`) was already stored — an idempotent insert
that never duplicates on replay (the DynamoDB adapter implements this via an
`EVT#<event_id>`/`DEDUPE` marker item, `adapters/persistence/
dynamo_observation_repository.py:58-62`) — and returns how many rows were newly
inserted. That count is what lets the core report accepted-vs-deduped without the
adapter leaking its persistence mechanism into the core.

`in_window` (STORY-011, dossier §11) is the READ side: it returns the raw
observations for one signal in `[since, until)` so the availability engine
(`core/queries/availability.py`) can derive availability% and completeness%
on demand. ALL SQL for this read stays behind the adapter implementing this
method — the core never sees a query.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime

from src.core.domain import SignalObservation


class ObservationRepository(ABC):
    """Persists canonical observations idempotently (dossier §6, §8)."""

    @abstractmethod
    def save_new(self, batch: Sequence[SignalObservation]) -> int:
        """Persist new observations from `batch`, skipping already-stored ones.

        Deduplication is by the observation's idempotency key; an observation seen
        before is silently skipped. Return the number of rows newly inserted.
        """
        raise NotImplementedError

    @abstractmethod
    def in_window(
        self, signal_key: str, since: datetime, until: datetime
    ) -> Sequence[SignalObservation]:
        """Return `signal_key`'s observations with `observed_at` in `[since, until)`.

        The half-open interval means adjacent windows never double-count the
        boundary instant. Order is unspecified — callers (the availability
        engine) group/sort as needed. This is the read side the dossier §11
        availability calculator derives from; no other read path exists, and
        the calculator persists nothing it computes here.
        """
        raise NotImplementedError
