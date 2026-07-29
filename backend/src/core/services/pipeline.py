"""Core logic pipeline, stages 1-3 (dossier §10) — pure, provider-blind.

`collapse` (stage 1) maps one signal's per-location observations for a single
cycle to one `Verdict`. `streak` (stage 2) counts consecutive same-health
verdicts reading backward over non-maintenance verdicts only. `anti_flap`
(stage 3) maps a `Streak` plus INJECTED per-app `AntiFlapThresholds` to an
`AntiFlapOutcome` — a proposed `ComponentStatus`, a distinct internal-warning
marker, or nothing. Nothing here mentions Dynatrace, Grail, or DQL — the
pipeline consumes canonical `SignalObservation`s and produces canonical
`Verdict`s, and would not change if the vendor were swapped (dossier §10).
Stage 4 (decide) is out of scope (STORY-024) — it needs the proposal
lifecycle / "current status" reads that anti-flap deliberately does not have.

This module imports ONLY `src.core.*` — no SQL, no vendor types, no I/O.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from pydantic import BaseModel, ConfigDict, model_validator

from src.core.domain import ComponentStatus, Health, SignalObservation, Verdict


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


class AntiFlapThresholds(BaseModel):
    """Per-app anti-flap streak-length thresholds (dossier §10), INJECTED.

    `anti_flap` never constructs this from config/DB — the
    `component -> app -> block` resolution that produces these values is
    config loading and is OUT OF SCOPE for this module (deferred to a later
    config story). The dossier §10 defaults are `major=5, partial=3,
    degraded=2, recovery=2`; callers that want them literally must supply
    them explicitly rather than relying on a hidden default here, so the
    injection boundary stays honest.
    """

    model_config = ConfigDict(frozen=True)

    major: int
    """FAILING streak length at/above which the proposed status is `major_outage`."""

    partial: int
    """FAILING streak length at/above which the proposed status is `partial_outage`."""

    degraded: int
    """FAILING streak length at/above which the proposed status is `degraded`."""

    recovery: int
    """PASSING streak length at/above which the proposed status is `operational`."""


class AntiFlapOutcome(BaseModel):
    """The result of one `anti_flap` call (dossier §10) — three distinguishable outcomes.

    Exactly one of three shapes, never conflated:
    - a proposed status: `proposed_status` is a `ComponentStatus`, `internal_warning` is `False`.
    - an internal warning: `proposed_status` is `None`, `internal_warning` is `True`. This is
      logged, NEVER published — it is not, and must never become, a `ComponentStatus`.
    - nothing: `proposed_status` is `None`, `internal_warning` is `False`.
    """

    model_config = ConfigDict(frozen=True)

    proposed_status: ComponentStatus | None
    """The status `decide` (stage 4, STORY-024) may act on; `None` if there is nothing to propose."""

    internal_warning: bool
    """`True` only for the single-failure internal-warning outcome; never paired with a status."""

    @model_validator(mode="after")
    def _require_status_warning_coherence(self) -> "AntiFlapOutcome":
        """Enforce the proposed-status<->internal-warning invariant this type represents.

        The internal-warning outcome is a distinct, unpublishable marker — it
        is logged, never acted on by `decide`, and must never be conflated
        with a proposed `ComponentStatus`. Rejecting the incoherent
        combination here, at construction, keeps a hand-built `AntiFlapOutcome`
        from reaching `decide` in a state that cannot be expressed cleanly
        (see class docstring).
        """
        if self.proposed_status is not None and self.internal_warning:
            raise ValueError(
                "proposed_status and internal_warning=True are mutually exclusive "
                "(an internal warning never carries a proposed status)"
            )
        return self


_NOTHING = AntiFlapOutcome(proposed_status=None, internal_warning=False)
_INTERNAL_WARNING = AntiFlapOutcome(proposed_status=None, internal_warning=True)


def _propose(status: ComponentStatus) -> AntiFlapOutcome:
    """Shared assembly for the "propose a status" outcome shape (never an internal warning)."""
    return AntiFlapOutcome(proposed_status=status, internal_warning=False)


def anti_flap(streak_: Streak, thresholds: AntiFlapThresholds) -> AntiFlapOutcome:
    """Map a `Streak` to an `AntiFlapOutcome` against INJECTED thresholds (dossier §10, stage 3).

    Pure lookup, no I/O, no config/DB read — `thresholds` is supplied by the caller (config
    loading and the `component -> app -> block` resolution are out of scope here). Branches on
    `streak_.health`:
    - `Health.DOWN` (failing): the severity ladder, checked most-severe-first so a streak that
      clears `major` is never mis-bucketed into `partial`/`degraded` — `length >= major` ->
      `major_outage`; else `length >= partial` -> `partial_outage`; else `length >= degraded` ->
      `degraded`; else a streak of exactly 1 -> an internal warning (logged, never published);
      else (e.g. length 0) -> nothing.
    - `Health.DEGRADED` (sustained degraded-performance): symmetric with the `DOWN` ladder's
      damping — `length >= degraded` -> `degraded`; else a streak of exactly 1 -> an internal
      warning (logged, never published); else (e.g. length 0) -> nothing. There is only one
      failing-adjacent bucket for this health (no `major`/`partial` escalation), but reaching it
      still requires the same streak length as the `DOWN` ladder's `degraded` rung.
    - `Health.UP` (passing): `length >= recovery` -> `operational`; else -> nothing (not yet
      confirmed recovered).
    """
    if streak_.health is Health.DOWN:
        if streak_.length >= thresholds.major:
            return _propose(ComponentStatus.MAJOR_OUTAGE)
        if streak_.length >= thresholds.partial:
            return _propose(ComponentStatus.PARTIAL_OUTAGE)
        if streak_.length >= thresholds.degraded:
            return _propose(ComponentStatus.DEGRADED)
        if streak_.length == 1:
            return _INTERNAL_WARNING
        return _NOTHING

    if streak_.health is Health.DEGRADED:
        if streak_.length >= thresholds.degraded:
            return _propose(ComponentStatus.DEGRADED)
        if streak_.length == 1:
            return _INTERNAL_WARNING
        return _NOTHING

    # Health.UP
    if streak_.length >= thresholds.recovery:
        return _propose(ComponentStatus.OPERATIONAL)
    return _NOTHING
