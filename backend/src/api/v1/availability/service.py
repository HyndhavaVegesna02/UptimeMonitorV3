"""Thin edge service for the availability feature (dossier §11, §13).

Resolves the AvailabilityCalculator via the container (observation_repo +
clock from app.state), applies window defaulting, maps domain result(s) →
DTO(s). No business logic here — all computation is in the core.

Per-signal interval resolution (dossier §11, §13, STORY-044 AC3/D5): a
caller-supplied `interval_seconds` wins outright (back-compat, no topology
lookup). Otherwise the signal's configured interval is read from the seeded
topology via `SignalRepository` — the 60s stopgap default this module used to
apply (and the stale "STORY-040 will supply per-signal config" comment) are
gone; an unconfigured/unknown signal is now an honest 404/409 rather than a
silent, wrong completeness% (audit finding H2).

Component-grain availability (dossier §11, §13, STORY-044 AC2, D4): computes
one `AvailabilityResult` per child signal (each with ITS OWN configured
interval) and rolls them up via the core's `rollup_group` — the maintenance
predicate is still a documented no-op stopgap (the real per-signal maintenance
predicate arrives with the maintenance-wiring story, not tied to a specific
closed story number).
"""

from datetime import datetime, timedelta

from fastapi import Depends

from src.api.dependencies import (
    get_clock,
    get_component_repo,
    get_observation_repo,
    get_signal_repo,
)
from src.api.v1._shared.windowing import DEFAULT_WINDOW_HOURS, resolve_window
from src.api.v1.availability.models import (
    AvailabilityDTO,
    ComponentAvailabilityDTO,
    SignalAvailabilityDTO,
)
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.topology import (
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)
from src.core.ports import (
    ClockPort,
    ComponentRepository,
    ObservationRepository,
    SignalRepository,
)
from src.core.queries.availability import (
    AvailabilityCalculator,
    AvailabilityResult,
    rollup_group,
)


def _resolve_window(
    *, since_str: str | None, until_str: str | None, now: datetime
) -> tuple[datetime, datetime, str]:
    """Resolve since/until/window label — shared by both endpoints (2026-06-25
    share-the-assembly agreement) so window defaulting has ONE home.

    until = clock.now() if not supplied; since = until − 24h if not supplied;
    window label is "24h" only when NEITHER was supplied, else the explicit
    ISO pair.
    """
    since, until = resolve_window(since_str, until_str, now)

    if since_str is None and until_str is None:
        window = f"{DEFAULT_WINDOW_HOURS}h"
    else:
        window = f"{since.isoformat()}..{until.isoformat()}"

    return since, until, window


def _to_dto(result: AvailabilityResult) -> AvailabilityDTO:
    """Map the core `AvailabilityResult` to the HTTP `AvailabilityDTO` — the
    domain type never leaks to the HTTP surface."""
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


def _no_maintenance(_at: datetime) -> bool:
    """No-op maintenance predicate (documented stopgap, dossier §13).

    The real per-signal maintenance predicate arrives with the
    maintenance-wiring story — this is deliberately not phrased as a promise
    tied to a specific closed story number (that was audit finding H2's other
    half: a stale "STORY-040 will supply" comment left in place after
    STORY-040 closed without doing it).
    """
    return False


class AvailabilityService:
    """Thin edge service: resolve window, call calculator, shape DTOs (dossier §13)."""

    def __init__(
        self,
        observation_repo: ObservationRepository,
        clock: ClockPort,
        component_repo: ComponentRepository,
        signal_repo: SignalRepository,
    ) -> None:
        self._observation_repo = observation_repo
        self._clock = clock
        self._component_repo = component_repo
        self._signal_repo = signal_repo

    def get_availability(
        self,
        signal_key: str,
        *,
        since_str: str | None,
        until_str: str | None,
        interval_seconds: int | None,
    ) -> AvailabilityDTO:
        """Compute per-signal availability and return as AvailabilityDTO.

        Interval resolution (STORY-044 AC3/D5):
          - caller supplied a positive `interval_seconds` → use it, NO
            topology lookup (back-compat: an unknown signal_key with an
            explicit interval keeps today's degenerate all-None 200).
          - caller supplied nothing → look up the signal's configured
            interval from the seeded topology: `SignalNotFoundError` if the
            signal_key isn't in the topology at all (maps to 404),
            `SignalIntervalUnconfiguredError` if the row exists but
            `interval_seconds IS NULL` (maps to 409).
        """
        now = self._clock.now()
        since, until, window = _resolve_window(
            since_str=since_str, until_str=until_str, now=now
        )

        if interval_seconds is not None:
            interval = timedelta(seconds=interval_seconds)
        else:
            signal = self._signal_repo.get(signal_key)
            if signal is None:
                raise SignalNotFoundError(
                    f"Signal {signal_key!r} not found in the seeded topology."
                )
            if signal.interval_seconds is None:
                raise SignalIntervalUnconfiguredError(
                    f"Signal {signal_key!r} has no configured interval_seconds."
                )
            interval = timedelta(seconds=signal.interval_seconds)

        calculator = AvailabilityCalculator(observation_repo=self._observation_repo)
        result = calculator.compute(
            signal_key,
            since=since,
            until=until,
            interval=interval,
            window=window,
            maintenance=_no_maintenance,
            computed_at=now,
        )

        return _to_dto(result)

    def get_component_availability(
        self,
        component_id: str,
        *,
        since_str: str | None,
        until_str: str | None,
    ) -> ComponentAvailabilityDTO:
        """Compute component-grain availability: the rollup plus per-signal
        children (dossier §11, STORY-044 AC2, D4).

        Each child uses ITS OWN configured interval — there is no interval
        query param on this endpoint. Raises `ComponentNotFoundError` for an
        unknown component id (maps to 404) and
        `SignalIntervalUnconfiguredError` if any child signal's
        `interval_seconds` is NULL (maps to 409; unreachable once the
        topology is fully seeded). A zero-signal component yields
        `signals: []` and the `rollup_group([])` degenerate (all-None
        percentages, zero counts) — never a 500.
        """
        component = self._component_repo.get(component_id)
        if component is None:
            raise ComponentNotFoundError(f"Component {component_id!r} not found.")

        now = self._clock.now()
        since, until, window = _resolve_window(
            since_str=since_str, until_str=until_str, now=now
        )

        children_signals = sorted(
            (
                signal
                for signal in self._signal_repo.list_signals()
                if signal.component_id == component_id
            ),
            key=lambda s: s.signal_key,
        )
        for signal in children_signals:
            if signal.interval_seconds is None:
                raise SignalIntervalUnconfiguredError(
                    f"Signal {signal.signal_key!r} has no configured interval_seconds."
                )

        calculator = AvailabilityCalculator(observation_repo=self._observation_repo)
        child_results: list[AvailabilityResult] = []
        child_dtos: list[SignalAvailabilityDTO] = []
        for signal in children_signals:
            result = calculator.compute(
                signal.signal_key,
                since=since,
                until=until,
                interval=timedelta(seconds=signal.interval_seconds),
                window=window,
                maintenance=_no_maintenance,
                computed_at=now,
            )
            child_results.append(result)
            child_dtos.append(
                SignalAvailabilityDTO(
                    signal_key=signal.signal_key,
                    **_to_dto(result).model_dump(),
                )
            )

        rollup_result = rollup_group(child_results, window=window, computed_at=now)

        return ComponentAvailabilityDTO(
            component_id=component_id,
            rollup=_to_dto(rollup_result),
            signals=child_dtos,
        )


def get_availability_service(
    observation_repo: ObservationRepository = Depends(get_observation_repo),
    clock: ClockPort = Depends(get_clock),
    component_repo: ComponentRepository = Depends(get_component_repo),
    signal_repo: SignalRepository = Depends(get_signal_repo),
) -> AvailabilityService:
    """Dependency provider for AvailabilityService (dossier §13)."""
    return AvailabilityService(
        observation_repo=observation_repo,
        clock=clock,
        component_repo=component_repo,
        signal_repo=signal_repo,
    )
