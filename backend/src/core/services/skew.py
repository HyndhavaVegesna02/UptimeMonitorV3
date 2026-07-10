"""The per-component skew flag (dossier §11 "Skew, surfaced" + Tier-2 T2.7).

Zone 4 / pure core. Split out of the availability calculator
(`core/queries/availability.py`) at refinement: skew is a cross-signal
WATERMARK comparison, distinct from the two-grain availability/completeness
math, and rides alongside completeness as a SEPARATE signal rather than a
field bolted onto `AvailabilityResult` — completeness can be low for reasons
that have nothing to do with any one feeder lagging its peers (dossier §11).

The flag is SET for any feeding signal whose watermark lags the MOST-RECENT
peer watermark (the freshest feeder in the set) by MORE than that signal's
own `interval`. Consistent with the established Zone 4 injection pattern
(STORY-010's `under_maintenance`, STORY-011's `interval`/`window`), the peer
set — each feeder's `signal_key`, watermark, and `interval` — is an INJECTED
input: no component->signals topology load and no DB/vendor/HTTP/SQL access
lives here (AC3). `skew` is compute-only and derive-on-read, like the
availability engine: it persists nothing.

This module imports ONLY `src.core.*` (in fact, only stdlib + pydantic) — no
SQL, no vendor types, no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timedelta

from pydantic import BaseModel, ConfigDict, model_validator


class SignalFeeder(BaseModel):
    """One feeding signal's current watermark + its own lag tolerance (dossier §11).

    `watermark` is `None` for a signal that has never advanced (AC4) — a
    freshly registered feeder with no observations yet is not the same as
    one reporting at some past instant. `interval` is the signal's own
    expected reporting cadence, INJECTED by the caller (mirroring
    `AvailabilityCalculator.compute`'s injected `interval`) — never read
    from per-app config here.
    """

    model_config = ConfigDict(frozen=True)

    signal_key: str
    """Stable signal name (dossier §5 vocabulary) — names this feeder in `SkewResult`."""

    watermark: datetime | None
    """This feeder's most recent observed instant; `None` if it has never advanced."""

    interval: timedelta
    """This feeder's own expected reporting cadence — its lag tolerance."""


class SkewResult(BaseModel):
    """The frozen result of one `skew` computation — a SEPARATE signal from
    `AvailabilityResult` (dossier §11, AC2).

    Never derived from completeness%: a component can be fully complete
    (every expected observation arrived) and still have a skewed feeder
    (one feeder's watermark itself lags its peers), and a component can have
    low completeness with no skew at all (sparse but evenly-paced feeders).
    `lagging_signals` names which feeders tripped the flag, in the INPUT
    order they were given, so a dashboard / proposal annotation can show
    them (dossier §11) — never just a bare boolean.
    """

    model_config = ConfigDict(frozen=True)

    skewed: bool
    """`True` iff at least one feeder in `lagging_signals` is lagging."""

    lagging_signals: tuple[str, ...]
    """The `signal_key`s of every feeder lagging its peers by more than its own `interval`."""

    @model_validator(mode="after")
    def _require_skewed_lagging_signals_coherence(self) -> "SkewResult":
        """Enforce the skewed<->lagging_signals invariant this type represents.

        `skewed` is true iff `lagging_signals` is non-empty: a flag with no
        named feeders, or named feeders with the flag unset, cannot be
        expressed cleanly (see class docstring). Rejecting the incoherent
        combination here, at construction, keeps a hand-built `SkewResult`
        from reaching a caller in a state `skew` itself never produces.
        """
        if self.skewed != bool(self.lagging_signals):
            raise ValueError(
                "skewed must equal bool(lagging_signals) "
                "(skewed=True requires a non-empty lagging_signals, "
                "and a non-empty lagging_signals requires skewed=True)"
            )
        return self


def skew(feeders: Sequence[SignalFeeder]) -> SkewResult:
    """Flag feeders lagging their peers' most-recent watermark (dossier §11, AC1).

    The reference is the MOST-RECENT peer watermark — the MAX `watermark`
    across `feeders` that actually have one. A feeder is skewed when
    `reference - feeder.watermark > feeder.interval` — lagging by EXACTLY
    its interval is NOT skewed (strict `>`, not `>=`; AC4 boundary). The
    feeder supplying the reference itself has zero lag and is never
    flagged.

    No-watermark rule (AC4, documented): a feeder with `watermark is None`
    can never SUPPLY the reference (it has nothing to compare peers
    against), but when at least one peer has a watermark, a never-advanced
    feeder is treated as MAXIMALLY lagging — i.e. skewed — since "no data
    yet" is at least as stale as any observed lag. If every feeder is
    watermark-less, there is no reference at all, so nothing can be
    flagged: no crash, no false positive.

    Degenerate inputs (AC4): an empty peer set, or a single-signal
    component (one feeder, no peers to lag behind), both yield
    `SkewResult(skewed=False, lagging_signals=())` — there is nothing to
    compare against, so nothing is skewed.
    """
    watermarked = [feeder for feeder in feeders if feeder.watermark is not None]

    if not watermarked or len(feeders) < 2:
        return SkewResult(skewed=False, lagging_signals=())

    reference = max(feeder.watermark for feeder in watermarked)

    lagging = tuple(
        feeder.signal_key
        for feeder in feeders
        if feeder.watermark is None or reference - feeder.watermark > feeder.interval
    )

    return SkewResult(skewed=bool(lagging), lagging_signals=lagging)
