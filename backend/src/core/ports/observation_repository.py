"""The observation repository port (dossier §6, §8) — durable, deduplicated store.

`save_new` persists a batch of canonical observations, skipping any whose
idempotency key (`source_event_id`) was already stored — the dossier specifies an
INSERT … ON CONFLICT DO NOTHING semantics — and returns how many rows were newly
inserted. That count is what lets the core report accepted-vs-deduped without the
adapter leaking SQL into the core.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence

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
