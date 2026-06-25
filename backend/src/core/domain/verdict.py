"""The canonical pipeline verdict (dossier §10, stages 1-2).

`Verdict` is the per-cycle output of stage 1 (`collapse`) and the per-element
input/output of stage 2 (`streak`). It represents EITHER a normal health
verdict for one signal's cycle, OR a maintenance marker — maintenance is
planned work, neither up nor down (V2 FR-8), so it short-circuits the rest of
the pipeline rather than carrying a health value.
"""

from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from src.core.domain.signal import Health


class Verdict(BaseModel):
    """One cycle's collapsed verdict for one signal (dossier §10).

    `observed_at` is the cycle instant — by convention the latest
    `observed_at` across the cycle's per-location observations
    (`max(observed_at)`), so the verdict timestamps to when the cycle's
    slowest-reporting location actually completed, never earlier.

    A maintenance cycle sets `under_maintenance=True` and leaves `health`
    unset (`None`): maintenance is excluded from the verdict (it is neither
    up nor down) and short-circuits the rest of the pipeline, so it never
    needs a health value. A normal verdict sets `under_maintenance=False`
    and always carries a `health`.
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    """Stable name identifying the signal this verdict was collapsed for."""

    observed_at: datetime
    """The cycle instant: `max(observed_at)` across the cycle's observations."""

    health: Health | None = None
    """Closed verdict for a normal cycle; `None` for a maintenance cycle."""

    under_maintenance: bool = False
    """True when this cycle is excluded from the verdict (planned work, V2 FR-8)."""

    @field_validator("observed_at")
    @classmethod
    def _require_utc(cls, value: datetime) -> datetime:
        """Reject naive or non-UTC timestamps, mirroring `SignalObservation` (dossier §5)."""
        if value.tzinfo is None or value.utcoffset() != timedelta(0):
            raise ValueError("observed_at must be a tz-aware UTC datetime")
        return value

    @model_validator(mode="after")
    def _require_maintenance_health_coherence(self) -> "Verdict":
        """Enforce the maintenance<->health invariant this type represents.

        A maintenance cycle (`under_maintenance=True`) is neither up nor down,
        so it must carry no health value; a normal cycle
        (`under_maintenance=False`) always has a closed verdict, so it must
        carry one. Rejecting the two incoherent shapes here, at construction,
        keeps a hand-built `Verdict` from reaching `streak` in a state that
        cannot be expressed cleanly (see module docstring).
        """
        if self.under_maintenance and self.health is not None:
            raise ValueError(
                "under_maintenance=True requires health=None "
                "(a maintenance cycle carries no health verdict)"
            )
        if not self.under_maintenance and self.health is None:
            raise ValueError(
                "under_maintenance=False requires a set health "
                "(a normal verdict always carries a closed health verdict)"
            )
        return self
