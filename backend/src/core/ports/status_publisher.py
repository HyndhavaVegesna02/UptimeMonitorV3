"""The status publisher port (dossier §6) — the core's outbound voice.

The core sends a canonical `StatusChange` carrying a canonical `component_id`,
never a Statuspage id. The adapter on the far side translates the component id and
the status to the vendor's vocabulary. This port exists for testability — a
recording fake in tests, the real publisher in production (dossier §6, §28).
"""

from abc import ABC, abstractmethod

from src.core.domain import StatusChange


class StatusPublisherPort(ABC):
    """Publishes a canonical status change for one component (dossier §6)."""

    @abstractmethod
    def publish(self, change: StatusChange) -> None:
        """Apply `change` to the published status surface for its component."""
        raise NotImplementedError
