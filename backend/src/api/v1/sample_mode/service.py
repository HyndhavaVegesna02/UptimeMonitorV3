"""Thin edge service for the sample-mode feature (dossier §13, STORY-048 D3).

TEMPORARY feature (PO directive, 2026-07-03) — see
`docs/scrum/wiki/sample-mode.md` for the REMOVAL inventory. Resolves
`SampleModeRepository` via the container and shapes the DTO response — no
business logic here (a bare bool read/write), mirroring the topology
feature's thin-service pattern.
"""

from fastapi import Depends

from src.api.dependencies import get_sample_mode_repo
from src.api.v1.sample_mode.models import SampleModeDTO
from src.core.ports.sample_mode_repository import SampleModeRepository


class SampleModeService:
    """Thin edge service: read/write the sample-mode flag, shape the DTO."""

    def __init__(self, sample_mode_repo: SampleModeRepository) -> None:
        self._sample_mode_repo = sample_mode_repo

    def get_state(self) -> SampleModeDTO:
        """Return the current flag state (`False` when never set)."""
        return SampleModeDTO(enabled=self._sample_mode_repo.is_enabled())

    def set_state(self, enabled: bool) -> SampleModeDTO:
        """Set the flag state (idempotent) and return the new state."""
        self._sample_mode_repo.set_enabled(enabled)
        return SampleModeDTO(enabled=enabled)


def get_sample_mode_service(
    sample_mode_repo: SampleModeRepository = Depends(get_sample_mode_repo),
) -> SampleModeService:
    """Dependency provider for SampleModeService (dossier §13)."""
    return SampleModeService(sample_mode_repo=sample_mode_repo)
