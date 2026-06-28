"""Controller for the history feature (dossier §13, §17).

GET /history?signal_key=...&since=...&until=...
Returns per-signal observation DTOs (most-recent first) via ObservationRepository.in_window.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.v1.history.models import ObservationDTO
from src.api.v1.history.service import HistoryService, get_history_service
from src.api.v1.history.validation import (
    SyntacticValidationError,
    validate_history_request,
)

router = APIRouter()


@router.get("/history", response_model=list[ObservationDTO])
def get_history(
    signal_key: str = Query(..., description="The signal key to retrieve history for"),
    since: str | None = Query(
        None, description="ISO-8601 window start (default: until − 24h)"
    ),
    until: str | None = Query(
        None, description="ISO-8601 window end (default: clock.now())"
    ),
    service: HistoryService = Depends(get_history_service),
) -> list[ObservationDTO]:
    """Return per-signal check history as ObservationDTOs, most-recent first (dossier §13, §17).

    Empty window → 200 + []. Missing signal_key → 422 before any core call.
    """
    try:
        validate_history_request(signal_key=signal_key, since=since, until=until)
    except SyntacticValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return service.get_history(signal_key, since_str=since, until_str=until)
