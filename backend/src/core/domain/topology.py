"""The seeded-topology signal read model (dossier §7, §9, STORY-044).

`Signal` is a vendor-neutral read model over the `signals` table row — distinct
from `core/domain/signal.py::SignalObservation`, which is one runtime monitor
execution. `Signal` never carries an observation; it carries the seeded
topology mapping (which component a signal feeds, at what cadence) the
`SignalRepository` port reads.
"""

from pydantic import BaseModel, ConfigDict, model_validator


class SignalNotFoundError(Exception):
    """Raised by the edge service (never the port) when a signal key the
    default-interval path needs is not in the seeded topology (dossier §13,
    STORY-044 D2/D5). Deliberately a plain `Exception`, not a `ValueError`
    subclass like `ComponentNotFoundError`/`ProposalNotFoundError` — the
    `SignalRepository` port itself never raises this; it returns `None` on an
    unknown key (mirrors `ComponentRepository.get`'s never-raises contract).
    """


class SignalIntervalUnconfiguredError(Exception):
    """Raised by the edge service when a signal exists in the topology but its
    `interval_seconds` is `NULL` (the D1 backfill predates this row, or the
    boot seed never ran) — distinct from `SignalNotFoundError`: the remedy is
    "re-seed", not "wrong key" (dossier §13, STORY-044 D2/D5).
    """


class Signal(BaseModel):
    """A seeded topology signal (dossier §7, §9, STORY-044 D2).

    Fields mirror the `signals` table's read-relevant columns. `component_id`
    is `None` for an orphan signal (not yet mapped to a component); the AC1
    topology endpoint is component-centric, so an orphan signal appears
    nowhere in its nesting. `interval_seconds` is `None` when the row
    predates the D1 backfill or a re-seed has not yet run — the calculator
    layer surfaces that honestly (`SignalIntervalUnconfiguredError`) rather
    than guessing a default.
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    name: str
    component_id: str | None
    interval_seconds: int | None

    @model_validator(mode="after")
    def _require_positive_interval_when_set(self) -> "Signal":
        """Enforce `interval_seconds > 0` when not `None` (2026-06-26 coherence agreement)."""
        if self.interval_seconds is not None and self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive when set")
        return self
