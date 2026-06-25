"""Core logic pipeline, stages 1-2 (dossier §10) — pure, provider-blind.

`collapse` (stage 1) maps one signal's per-location observations for a single
cycle to one `Verdict`. `streak` (stage 2, added in a later step) counts
consecutive same-health verdicts reading backward. Nothing here mentions
Dynatrace, Grail, or DQL — the pipeline consumes canonical `SignalObservation`s
and produces canonical `Verdict`s, and would not change if the vendor were
swapped (dossier §10).

This module imports ONLY `src.core.*` — no SQL, no vendor types, no I/O.
"""

from __future__ import annotations

from collections.abc import Sequence

from src.core.domain import Health, SignalObservation, Verdict


def collapse(
    observations: Sequence[SignalObservation], *, under_maintenance: bool
) -> Verdict:
    """Collapse one cycle's per-location observations to a single `Verdict` (dossier §10).

    Assumes every observation in `observations` belongs to one signal and one
    cycle (the caller groups across cycles/signals; this function does not).
    `under_maintenance` is an INJECTED boolean — never a DB/table lookup — so
    the function stays pure; a fake/predicate supplies it in tests and, later,
    the composition layer.

    The cycle instant is `max(observed_at)` across the cycle's observations,
    timestamping the verdict to when the slowest-reporting location actually
    completed.
    """
    cycle_instant = max(observation.observed_at for observation in observations)
    signal_key = observations[0].signal_key

    if under_maintenance:
        return Verdict(
            signal_key=signal_key,
            observed_at=cycle_instant,
            health=None,
            under_maintenance=True,
        )

    health = Health.UP

    return Verdict(
        signal_key=signal_key,
        observed_at=cycle_instant,
        health=health,
        under_maintenance=False,
    )
