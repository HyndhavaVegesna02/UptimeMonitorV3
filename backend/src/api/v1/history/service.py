"""Thin edge service for the history feature (dossier §13, §17).

Resolves ObservationRepository via the container (observation_repo + clock from
app.state), applies window defaulting, calls in_window, maps domain types →
ObservationDTOs sorted most-recent first. No business logic here.
"""

from fastapi import Depends

from src.api.dependencies import get_clock, get_observation_repo
from src.api.v1._shared.windowing import resolve_window
from src.api.v1.history.models import ObservationDTO
from src.core.ports import ClockPort, ObservationRepository


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
        limit: int | None = None,
    ) -> list[ObservationDTO]:
        """Return per-signal observations as DTOs, most-recent first.

        Window defaulting (AC3, dossier §17):
          until = clock.now() if not supplied
          since = until − 24 h if not supplied

        `limit` (STORY-094): when supplied, caps the result to the N most
        recent observations — the cap is applied AFTER the most-recent-first
        sort, by slicing it. `None` (absent) leaves the full window untouched.
        The ObservationRepository port is unchanged: the cap is edge-side.
        """
        now = self._clock.now()
        since, until = resolve_window(since_str, until_str, now)

        observations = self._observation_repo.in_window(signal_key, since, until)

        # Sort most-recent first; map to DTOs (omit source/raw_ref/source_event_id)
        sorted_obs = sorted(observations, key=lambda o: o.observed_at, reverse=True)
        if limit is not None:
            sorted_obs = sorted_obs[:limit]
        return [
            ObservationDTO(
                signal_key=o.signal_key,
                observed_at=o.observed_at,
                health=o.health.value,
                location=o.location,
                latency_ms=o.latency_ms,
                response_status_code=o.response_status_code,
                check_type=o.source.native_kind,
            )
            for o in sorted_obs
        ]


def get_history_service(
    observation_repo: ObservationRepository = Depends(get_observation_repo),
    clock: ClockPort = Depends(get_clock),
) -> HistoryService:
    """Dependency provider for HistoryService (dossier §13)."""
    return HistoryService(observation_repo=observation_repo, clock=clock)
