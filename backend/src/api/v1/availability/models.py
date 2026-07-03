"""Pydantic DTOs for the availability API feature (dossier §11, §13).

`AvailabilityDTO` mirrors `core/services/availability.py::AvailabilityResult`
fields but is a distinct DTO — never the domain result type itself.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AvailabilityDTO(BaseModel):
    """Data Transfer Object for one per-signal availability computation (dossier §11, §13).

    Mirrors `AvailabilityResult`'s fields; the domain type never leaks to the
    HTTP surface — callers see only this DTO.
    """

    model_config = ConfigDict(frozen=True)

    availability_pct: float | None
    """Passing ÷ (total − maintenance) over collapsed verdicts; None if degenerate."""

    completeness_pct: float | None
    """Actual ÷ (intervals × distinct_locations) over raw observations; None if degenerate."""

    total_verdicts: int
    """Count of cycles collapsed in the window (includes maintenance and gaps)."""

    passing_verdicts: int
    """Count of verdicts with health == Health.UP (non-maintenance)."""

    maintenance_verdicts: int
    """Count of verdicts with under_maintenance=True — excluded from both sides."""

    gap_verdicts: int
    """Count of expected-but-missing cycles — excluded from the denominator."""

    distinct_locations: int
    """COUNT(DISTINCT location) observed in the window."""

    window: str
    """The window label this result was computed over (e.g. "24h" or explicit ISO range)."""

    computed_at: datetime
    """The instant this result was derived."""


class SignalAvailabilityDTO(AvailabilityDTO):
    """One child signal's availability, nested under a component rollup
    (dossier §11, §13, STORY-044 AC2). Adds `signal_key` to `AvailabilityDTO`
    so a component-grain response can name which signal each child is.
    """

    signal_key: str
    """The child signal's key — names which signal this child result is for."""


class ComponentAvailabilityDTO(BaseModel):
    """Component-grain availability: the rollup plus each per-signal child
    (dossier §11, §13, STORY-044 AC2). Lets a single call render BOTH the
    two-grain Availability tab's component and signal rows.
    """

    model_config = ConfigDict(frozen=True)

    component_id: str
    """The component this result is for."""

    rollup: AvailabilityDTO
    """`rollup_group` of the children: MIN of non-None percentages, SUM of counts."""

    signals: list[SignalAvailabilityDTO]
    """The per-signal children, sorted by `signal_key`. Empty for a
    zero-signal component — `rollup` is then the `rollup_group([])` degenerate
    (all-None percentages, zero counts), never a 500."""
