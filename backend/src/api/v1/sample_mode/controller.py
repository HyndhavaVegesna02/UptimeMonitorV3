"""Controller for the sample-mode feature (dossier §13, STORY-048 D3, AC2).

TEMPORARY feature — see docs/scrum/wiki/sample-mode.md for the REMOVAL
inventory.

GET /sample-mode  -> current flag state.
PUT /sample-mode  -> set the flag (idempotent); returns the new state.
"""

from fastapi import APIRouter, Depends

from src.api.v1.sample_mode.models import SampleModeDTO, SampleModeUpdateRequest
from src.api.v1.sample_mode.service import SampleModeService, get_sample_mode_service

router = APIRouter()


@router.get("/sample-mode", response_model=SampleModeDTO)
def get_sample_mode(
    service: SampleModeService = Depends(get_sample_mode_service),
) -> SampleModeDTO:
    """Return the current sample-mode flag state (`enabled: false` when never set)."""
    return service.get_state()


@router.put("/sample-mode", response_model=SampleModeDTO)
def set_sample_mode(
    request: SampleModeUpdateRequest,
    service: SampleModeService = Depends(get_sample_mode_service),
) -> SampleModeDTO:
    """Set the sample-mode flag (idempotent); returns the new state."""
    return service.set_state(request.enabled)
