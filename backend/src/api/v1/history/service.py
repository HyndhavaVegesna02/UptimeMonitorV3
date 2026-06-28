"""Thin edge service for the history feature (dossier §13, §17).

Resolves ObservationRepository via the container (observation_repo + clock from
app.state), applies window defaulting, calls in_window, maps domain types →
ObservationDTOs sorted most-recent first. No business logic here.
"""

from datetime import timedelta

from fastapi import Depends

from src.api.dependencies import get_clock, get_observation_repo
from src.api.v1.history.models import ObservationDTO
from src.core.ports import ClockPort, ObservationRepository

_DEFAULT_WINDOW_HOURS = 24


class HistoryService:
    """Thin edge service: resolve window, call in_window, shape DTOs (dossier §13)."""

    def __init__(
        self,
        observation_repo: ObservationRepository,
        clock: ClockPort,
    ) -> None:
        self._observation_repo = observation_repo
        self._clock = clock

    def get_history(
        self,
        signal_key: str,
        *,
        since_str: str | None,
        until_str: str | None,
    ) -> list[ObservationDTO]:
        """Return per-signal observations as DTOs, most-recent first.

        Window defaulting (AC3, dossier §17):
          until = clock.now() if not supplied
          since = until − 24 h if not supplied
        """
        from datetime import datetime

        now = self._clock.now()

        if until_str is not None:
            until = datetime.fromisoformat(until_str)
        else:
            until = now

        if since_str is not None:
            since = datetime.fromisoformat(since_str)
        else:
            since = until - timedelta(hours=_DEFAULT_WINDOW_HOURS)

        observations = self._observation_repo.in_window(signal_key, since, until)

        # Sort most-recent first; map to DTOs (omit source/raw_ref/source_event_id)
        sorted_obs = sorted(observations, key=lambda o: o.observed_at, reverse=True)
        return [
            ObservationDTO(
                signal_key=o.signal_key,
                observed_at=o.observed_at,
                health=o.health.value,
                location=o.location,
                latency_ms=o.latency_ms,
            )
            for o in sorted_obs
        ]


def get_history_service(
    observation_repo: ObservationRepository = Depends(get_observation_repo),
    clock: ClockPort = Depends(get_clock),
) -> HistoryService:
    """Dependency provider for HistoryService (dossier §13)."""
    return HistoryService(observation_repo=observation_repo, clock=clock)
