"""Controller for the availability feature (dossier §11, §13).

GET /availability?signal_key=...&since=...&until=...&interval_seconds=...
Returns per-signal AvailabilityDTO computed by AvailabilityCalculator (dossier §11).

GET /availability/component/{component_id}?since=...&until=...
Returns component-grain availability: the rollup_group plus per-signal
children, each computed with its own configured interval (STORY-044 AC2).
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.v1.availability.models import AvailabilityDTO, ComponentAvailabilityDTO
from src.api.v1.availability.service import (
    AvailabilityService,
    get_availability_service,
)
from src.api.v1.availability.validation import (
    SyntacticValidationError,
    validate_availability_request,
    validate_component_availability_request,
)
from src.core.domain.component import ComponentNotFoundError
from src.core.domain.topology import (
    SignalIntervalUnconfiguredError,
    SignalNotFoundError,
)

router = APIRouter()


@router.get("/availability", response_model=AvailabilityDTO)
def get_availability(
    signal_key: str = Query(
        ..., description="The signal key to compute availability for"
    ),
    since: str | None = Query(
        None, description="ISO-8601 window start (default: until − 24h)"
    ),
    until: str | None = Query(
        None, description="ISO-8601 window end (default: clock.now())"
    ),
    interval_seconds: int | None = Query(
        None,
        description=(
            "Cycle interval in seconds; defaults to the signal's configured "
            "interval from the seeded topology"
        ),
        gt=0,
    ),
    service: AvailabilityService = Depends(get_availability_service),
) -> AvailabilityDTO:
    """Return per-signal availability% and completeness% (dossier §11, §13).

    Computes via AvailabilityCalculator over the requested window.
    No-data window → availability_pct=None / completeness_pct=None (not 500).
    An unknown signal_key on the default-interval path → 404; a seeded signal
    with no configured interval → 409 (STORY-044 AC3).
    """
    try:
        validate_availability_request(
            signal_key=signal_key,
            since=since,
            until=until,
            interval_seconds=interval_seconds,
        )
    except SyntacticValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    try:
        return service.get_availability(
            signal_key,
            since_str=since,
            until_str=until,
            interval_seconds=interval_seconds,
        )
    except SignalNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except SignalIntervalUnconfiguredError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e


@router.get(
    "/availability/component/{component_id}", response_model=ComponentAvailabilityDTO
)
def get_component_availability(
    component_id: str,
    since: str | None = Query(
        None, description="ISO-8601 window start (default: until − 24h)"
    ),
    until: str | None = Query(
        None, description="ISO-8601 window end (default: clock.now())"
    ),
    service: AvailabilityService = Depends(get_availability_service),
) -> ComponentAvailabilityDTO:
    """Return component-grain availability (dossier §11, §13, STORY-044 AC2).

    The `rollup_group` result plus the per-signal children, each computed
    with that signal's OWN configured interval (no interval query param on
    this endpoint). Unknown component id → 404. A no-data window surfaces
    nulls, not a 500. A child signal with no configured interval → 409
    (unreachable once fully seeded).
    """
    try:
        validate_component_availability_request(
            component_id=component_id, since=since, until=until
        )
    except SyntacticValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    try:
        return service.get_component_availability(
            component_id, since_str=since, until_str=until
        )
    except ComponentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except SignalIntervalUnconfiguredError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
