"""Thin edge service for the availability feature (dossier §11, §13).

Resolves the AvailabilityCalculator via the container (observation_repo +
clock from app.state), applies window defaulting, maps domain result →
AvailabilityDTO. No business logic here — all computation is in the core.

Per-signal stopgaps (documented, not silently hardcoded):
  - `interval` is resolved from the caller-supplied `interval_seconds` query
    param (default 60 s) until STORY-040 provides per-signal config.
  - `maintenance` is a no-op `lambda _at: False` because the signal→component
    mapping does not yet exist (STORY-040). Once the topology layer lands, the
    composition root will resolve the real maintenance predicate per signal key.
"""

from datetime import datetime, timedelta

from fastapi import Depends

from src.api.dependencies import get_clock, get_observation_repo
from src.api.v1.availability.models import AvailabilityDTO
from src.core.ports import ClockPort, ObservationRepository
from src.core.services.availability import AvailabilityCalculator

_DEFAULT_INTERVAL_SECONDS = 60
_DEFAULT_WINDOW_HOURS = 24


class AvailabilityService:
    """Thin edge service: resolve window, call calculator, shape DTO (dossier §13)."""

    def __init__(
        self,
        observation_repo: ObservationRepository,
        clock: ClockPort,
    ) -> None:
        self._observation_repo = observation_repo
        self._clock = clock

    def get_availability(
        self,
        signal_key: str,
        *,
        since_str: str | None,
        until_str: str | None,
        interval_seconds: int,
    ) -> AvailabilityDTO:
        """Compute per-signal availability and return as AvailabilityDTO.

        Window defaulting (AC3, dossier §11):
          until = clock.now() if not supplied
          since = until − 24 h if not supplied
          computed_at = clock.now()

        Stopgaps until STORY-040 (documented per plan):
          interval ← timedelta(seconds=interval_seconds) [default 60]
          maintenance ← lambda _at: False (no signal→component mapping yet)
        """
        now = self._clock.now()

        # Resolve until / since
        if until_str is not None:
            until = datetime.fromisoformat(until_str)
        else:
            until = now

        if since_str is not None:
            since = datetime.fromisoformat(since_str)
        else:
            since = until - timedelta(hours=_DEFAULT_WINDOW_HOURS)

        # Window label
        if since_str is None and until_str is None:
            window = f"{_DEFAULT_WINDOW_HOURS}h"
        else:
            window = f"{since.isoformat()}..{until.isoformat()}"

        # Stopgap: interval from caller param (STORY-040 will supply per-signal config)
        interval = timedelta(seconds=interval_seconds)

        # Stopgap: maintenance no-op (STORY-040 will wire signal→component mapping)
        def maintenance(_at: datetime) -> bool:
            return False

        calculator = AvailabilityCalculator(observation_repo=self._observation_repo)
        result = calculator.compute(
            signal_key,
            since=since,
            until=until,
            interval=interval,
            window=window,
            maintenance=maintenance,
            computed_at=now,
        )

        return AvailabilityDTO(
            availability_pct=result.availability_pct,
            completeness_pct=result.completeness_pct,
            total_verdicts=result.total_verdicts,
            passing_verdicts=result.passing_verdicts,
            maintenance_verdicts=result.maintenance_verdicts,
            gap_verdicts=result.gap_verdicts,
            distinct_locations=result.distinct_locations,
            window=result.window,
            computed_at=result.computed_at,
        )


def get_availability_service(
    observation_repo: ObservationRepository = Depends(get_observation_repo),
    clock: ClockPort = Depends(get_clock),
) -> AvailabilityService:
    """Dependency provider for AvailabilityService (dossier §13)."""
    return AvailabilityService(observation_repo=observation_repo, clock=clock)
