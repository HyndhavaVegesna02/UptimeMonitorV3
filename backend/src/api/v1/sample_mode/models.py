"""Pydantic DTOs for the sample-mode API feature (dossier §13, STORY-048 D3).

TEMPORARY feature (PO directive, 2026-07-03) — see
`docs/scrum/wiki/sample-mode.md` for the REMOVAL inventory.
"""

from pydantic import BaseModel, ConfigDict


class SampleModeDTO(BaseModel):
    """The current sample-mode flag state (dossier §13, STORY-048 D3)."""

    model_config = ConfigDict(frozen=True)

    enabled: bool


class SampleModeUpdateRequest(BaseModel):
    """DTO for the incoming PUT body that sets the flag (STORY-048 D3)."""

    model_config = ConfigDict(frozen=True)

    enabled: bool
