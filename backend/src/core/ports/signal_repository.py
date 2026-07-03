"""The signal repository port (dossier §7, §9, STORY-044 D2) — persistence for
the seeded-topology signal read model.

Read-only: `SignalRepository` never writes — the seed (`composition/seed.py`)
is the only writer of `signals`. Mirrors `ComponentRepository.get`'s
never-raises, `None`-on-unknown contract (2026-06-26 fake/adapter parity
agreement).
"""

from abc import ABC, abstractmethod

from src.core.domain.topology import Signal


class SignalRepository(ABC):
    """Port interface for reading seeded-topology signals (dossier §7, §9)."""

    @abstractmethod
    def list_signals(self) -> list[Signal]:
        """Retrieve every seeded signal, ordered by `signal_key` (deterministic).

        Returns:
            list[Signal]: All signals, or `[]` if none exist. Never raises.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, signal_key: str) -> Signal | None:
        """Retrieve a single signal by its key.

        Returns `None` when no signal with `signal_key` exists — never
        raises, never a sentinel value (mirrors `ComponentRepository.get`,
        2026-06-26 parity agreement).
        """
        raise NotImplementedError
