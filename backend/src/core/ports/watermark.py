"""The watermark repository port (dossier §6, §8) — the core-owned cursor.

The watermark is the per-signal ingestion cursor: the instant up to which the
core has already accepted observations for a given signal. It is OWNED by the
core (not the adapter) and advances only after a commit, only over accepted
observations (dossier §8) — that ordering is what makes ingestion crash-safe.
This port is the persistence interface for that cursor; a real database
implements it in Zone 3.
"""

from abc import ABC, abstractmethod
from datetime import datetime


class WatermarkRepository(ABC):
    """Stores and advances the per-signal ingestion watermark (dossier §6, §8)."""

    @abstractmethod
    def get(self, signal_key: str) -> datetime | None:
        """Return the watermark for `signal_key`, or None if it has never advanced."""
        raise NotImplementedError

    @abstractmethod
    def advance(self, signal_key: str, to: datetime) -> None:
        """Move the watermark for `signal_key` forward to instant `to`."""
        raise NotImplementedError
