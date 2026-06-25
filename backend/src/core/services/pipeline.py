"""Core logic pipeline, stages 1-2 (dossier §10) — pure, provider-blind.

`collapse` (stage 1) maps one signal's per-location observations for a single
cycle to one `Verdict`. `streak` (stage 2) counts consecutive same-health
verdicts reading backward over non-maintenance verdicts only. Nothing here
mentions Dynatrace, Grail, or DQL — the pipeline consumes canonical
`SignalObservation`s and produces canonical `Verdict`s, and would not change
if the vendor were swapped (dossier §10). Stages 3-4 (anti-flap + decide) are
out of scope (STORY-024).

This module imports ONLY `src.core.*` — no SQL, no vendor types, no I/O.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from pydantic import BaseModel, ConfigDict

from src.core.domain import Health, SignalObservation, Verdict


class Streak(BaseModel):
    """The current streak: `length` consecutive verdicts of `health` (dossier §10).

    Read off the most recent NON-maintenance verdict's health, counting
    backward over non-maintenance verdicts only. Governs the displayed
    status; never the availability ratio (P4 / D-3).
    """

    model_config = ConfigDict(frozen=True)

    health: Health
    length: int


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

    Raises `ValueError` if `observations` is empty — there is no cycle instant
    or signal key to collapse from. The symmetric empty-input case for
    `streak` returns `None` instead, since `streak` always has a well-defined
    "no streak yet" answer; `collapse` has no equivalent default `Verdict`.
    """
    if not observations:
        raise ValueError("collapse requires at least one observation for a cycle")

    cycle_instant = max(observation.observed_at for observation in observations)
    signal_key = observations[0].signal_key

    if under_maintenance:
        return Verdict(
            signal_key=signal_key,
            observed_at=cycle_instant,
            health=None,
            under_maintenance=True,
        )

    health = _collapse_health(observation.health for observation in observations)

    return Verdict(
        signal_key=signal_key,
        observed_at=cycle_instant,
        health=health,
        under_maintenance=False,
    )


def _collapse_health(healths: Iterable[Health]) -> Health:
    """Apply the §10 collapse rule to a cycle's per-location health values.

    All `up` -> `up`; all `down` -> `down`; anything else (a mix, or every
    observation `degraded`) -> `degraded`. Any non-up value alongside others
    is enough to drag the cycle to `degraded` rather than `down`.
    """
    distinct = set(healths)

    if distinct == {Health.UP}:
        return Health.UP
    if distinct == {Health.DOWN}:
        return Health.DOWN
    return Health.DEGRADED


def streak(verdicts: Sequence[Verdict]) -> Streak | None:
    """Count the current streak reading backward over `verdicts` (dossier §10).

    `verdicts` is ordered oldest-to-newest (the natural cycle order); this
    reads it from the end. Maintenance verdicts are skipped entirely — they
    are excluded from the sequence the streak reads and do not themselves
    break a run, since a maintenance verdict simply never participates.
    Counting starts from the most recent NON-maintenance verdict's health and
    continues backward while consecutive non-maintenance verdicts match it; a
    health change terminates the streak. Returns `None` if there is no
    non-maintenance verdict to start from.
    """
    non_maintenance = [v for v in verdicts if not v.under_maintenance]
    if not non_maintenance:
        return None

    current_health = non_maintenance[-1].health
    length = 0
    for verdict in reversed(non_maintenance):
        if verdict.health != current_health:
            break
        length += 1

    return Streak(health=current_health, length=length)
