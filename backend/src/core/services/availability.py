"""The availability engine — two-grain math + group rollup (dossier §11).

Zone 4 / pure core. The system's first CALCULATOR: compute-only, no tables,
part of the constant core. It reads observations through the
`ObservationRepository.in_window` port and computes two percentages on
demand, persisting nothing (D-1). It runs in parallel to the four-stage
pipeline (`core/services/pipeline.py`) and never consults the streak (P4).

Two metrics, two grains, never sharing a denominator:
  - Availability % is computed over COLLAPSED VERDICTS (cycles): `passing ÷
    (total − maintenance)`. `up` passes; `down`/`degraded` don't; maintenance
    is excluded BOTH sides; gaps are excluded from the denominator (the
    default `exclude` policy). Reuses `collapse` (STORY-010).
  - Completeness % is computed over RAW OBSERVATIONS: `actual ÷ (intervals ×
    distinct_locations)` where `intervals = window ÷ interval` and
    `distinct_locations = COUNT(DISTINCT location)`. The location-aware
    denominator is the multi-location fix: it stops a 3-location signal
    reporting 300% completeness.

This module imports ONLY `src.core.*` — no SQL, no vendor types, no I/O. The
skew flag (dossier §11 "Skew, surfaced") is OUT OF SCOPE here (STORY-026).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AvailabilityResult(BaseModel):
    """The frozen result of one availability computation (dossier §11).

    Two independent percentages at deliberately different grains
    (`availability_pct` over verdicts, `completeness_pct` over observations),
    plus the counts that produced them, for auditability. Either percentage
    is `None` when its denominator is degenerate (AC6) — e.g. a window with
    zero observations has no verdicts to judge, so `availability_pct` is
    `None` rather than a misleading `0.0`; a zero completeness denominator
    (no observations, hence no distinct locations) is `None` rather than a
    `ZeroDivisionError`.
    """

    model_config = ConfigDict(frozen=True)

    availability_pct: float | None
    """`passing ÷ (total − maintenance)` over collapsed verdicts; `None` if degenerate."""

    completeness_pct: float | None
    """`actual ÷ (intervals × distinct_locations)` over raw observations; `None` if degenerate."""

    total_verdicts: int
    """Count of cycles collapsed in the window (includes maintenance and gaps)."""

    passing_verdicts: int
    """Count of verdicts with `health == Health.UP` (non-maintenance)."""

    maintenance_verdicts: int
    """Count of verdicts with `under_maintenance=True` — excluded from both sides."""

    gap_verdicts: int
    """Count of expected-but-missing cycles — excluded from the denominator (`exclude` policy)."""

    distinct_locations: int
    """`COUNT(DISTINCT location)` observed in the window — makes the completeness
    denominator auditable; 0 when the window has no observations at all."""

    window: str
    """The window label this result was computed over (caller-supplied, e.g. "24h")."""

    computed_at: datetime
    """The instant this result was derived — always "now", since nothing is cached or stored."""
