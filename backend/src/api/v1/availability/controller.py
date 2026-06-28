"""Controller for the availability feature (dossier §11, §13).

GET /availability?signal_key=...&since=...&until=...&interval_seconds=...
Returns per-signal AvailabilityDTO computed by AvailabilityCalculator (dossier §11).
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.v1.availability.models import AvailabilityDTO
from src.api.v1.availability.service import (
    AvailabilityService,
    get_availability_service,
)
from src.api.v1.availability.validation import (
    SyntacticValidationError,
    validate_availability_request,
)

router = APIRouter()

_DEFAULT_INTERVAL_SECONDS = 60


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
    interval_seconds: int = Query(
        _DEFAULT_INTERVAL_SECONDS,
        description="Cycle interval in seconds (stopgap default 60; STORY-040 will supply per-signal config)",
        gt=0,
    ),
    service: AvailabilityService = Depends(get_availability_service),
) -> AvailabilityDTO:
    """Return per-signal availability% and completeness% (dossier §11, §13).

    Computes via AvailabilityCalculator over the requested window.
    No-data window → availability_pct=None / completeness_pct=None (not 500).
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

    return service.get_availability(
        signal_key,
        since_str=since,
        until_str=until,
        interval_seconds=interval_seconds,
    )
