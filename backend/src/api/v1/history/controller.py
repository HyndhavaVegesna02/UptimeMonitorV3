"""Controller for the history feature (dossier §13, §17).

GET /history?signal_key=...&since=...&until=...&limit=...
Returns per-signal observation DTOs (most-recent first) via ObservationRepository.in_window.
`limit` (STORY-094) is an optional server-side cap applied AFTER the most-recent-first
sort; absent, behavior is unchanged (full window).
"""

from fastapi import APIRouter, Depends, Query

from src.api.v1.history.models import ObservationDTO
from src.api.v1.history.service import HistoryService, get_history_service
from src.api.v1.history.validation import (
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
    limit: int | None = Query(
        None,
        ge=1,
        description=(
            "Optional cap on the number of observations returned, applied "
            "after the most-recent-first sort (STORY-094). Absent = full window."
        ),
    ),
    service: HistoryService = Depends(get_history_service),
) -> list[ObservationDTO]:
    """Return per-signal check history as ObservationDTOs, most-recent first (dossier §13, §17).

    Empty window → 200 + []. Missing signal_key → 422 before any core call.
    `limit` (STORY-094): int >= 1 caps the result to the N most recent
    observations; `ge=1` plus FastAPI's int coercion yield 422 on 0/negative/
    non-int values before any core call.
    """
    validate_history_request(signal_key=signal_key, since=since, until=until)

    return service.get_history(
        signal_key, since_str=since, until_str=until, limit=limit
    )
