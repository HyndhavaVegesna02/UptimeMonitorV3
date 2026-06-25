"""The rejected-observation repository port (dossier §6, §8) — the quarantine sink.

An observation that fails the ingest validation gate (dossier §8, §14 T1.3) is
never silently dropped: it is written here with a reason and its raw payload
for audit, while the rest of the batch proceeds. `signal_key` may be unknown or
absent — that is often exactly *why* the observation was rejected — so this
port (and its persistence) must accept a quarantine row even when the signal
isn't (yet) part of seeded topology.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class RejectedObservationRepository(ABC):
    """Quarantines invalid observations instead of dropping them (dossier §6, §8)."""

    @abstractmethod
    def save(
        self,
        *,
        signal_key: str | None,
        reason: str,
        payload: dict,
        rejected_at: datetime,
    ) -> None:
        """Persist one rejected observation for audit.

        `payload` is the raw rejected observation (as a dict) so the original
        shape is recoverable; `reason` names why the validation gate refused
        it. Rejection is never a poison pill — the caller persists this and
        moves on to the rest of the batch.
        """
        raise NotImplementedError
