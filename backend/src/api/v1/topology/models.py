"""Pydantic DTOs for the topology API feature (dossier §7, §9, §13, STORY-044 AC1).

`TopologySignalDTO`/`ComponentTopologyDTO` are shaped for the AC1 payload —
distinct from the `Signal`/`Component` domain types, which never leak to the
HTTP surface.
"""

from pydantic import BaseModel, ConfigDict


class TopologySignalDTO(BaseModel):
    """One signal nested under its component (dossier §7, §9, STORY-044 AC1)."""

    model_config = ConfigDict(frozen=True)

    signal_key: str
    name: str
    interval_seconds: int | None
    """`None` when the seeded row predates the D1 backfill or a re-seed has
    not yet run — surfaced honestly, never a guessed default."""

    component_id: str
    """The owning component's id — inside a component group this is always
    that component's own id (the AC names component_id per-signal)."""


class ComponentTopologyDTO(BaseModel):
    """One component with its nested signals (dossier §7, §9, STORY-044 AC1).

    Status/availability are deliberately NOT in this payload (the Dashboard
    already has `/components`; component-grain availability is the D4
    `/availability/component/{component_id}` endpoint).
    """

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    signals: list[TopologySignalDTO]
