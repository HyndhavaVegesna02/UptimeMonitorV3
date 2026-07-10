"""Pipeline orchestrator — composition-zone wiring (STORY-016a, dossier §8/§10/§12).

This module is composition wiring ONLY. Every domain rule lives in the core
services it calls (``collapse``, ``streak``, ``anti_flap``, ``DecideService``).
This module:

* reads config + observations (§8 step 5),
* buckets them into cycles (§11 / §10),
* collapses per cycle (§10 stage 1),
* runs streak + anti-flap (§10 stages 2-3),
* delegates to ``DecideService`` (§12 / §10 stage 4).

Architecture constraint (dossier §4): composition zone may import BOTH
``src.core`` and ``src.adapters``; core must NOT import from here.
No new import-linter contract is added — the orchestrator is wiring, not a
new domain service.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from src.composition.config import Config
from src.core.ports.clock import ClockPort
from src.core.ports.component_repository import ComponentRepository
from src.core.ports.maintenance_repository import MaintenanceRepository
from src.core.ports.observation_repository import ObservationRepository
from src.core.queries.availability import bucket_into_cycles
from src.core.services.decide import DecideAction, DecideService
from src.core.services.pipeline import anti_flap, collapse, streak

_log = logging.getLogger(__name__)


def orchestrate_signal(
    *,
    signal_key: str,
    config: Config,
    observation_repo: ObservationRepository,
    maintenance_repo: MaintenanceRepository,
    component_repo: ComponentRepository,
    decide_service: DecideService,
    clock: ClockPort,
) -> DecideAction:
    """Run the §8/§10/§12 pipeline for one signal → return the decide action.

    Algorithm (plan.md 2026-06-28):
    1. Resolve ``component_id``, ``thresholds``, and ``interval`` from config.
    2. Compute the observation window:
       ``until = clock.now()``
       ``since = until − (max(thresholds) + 2) × interval``
       (enough cycles for any threshold; the +2 gives one cycle of slack on
       each side — consistent with dossier §8 "overlap for edge cadence").
    3. Read ``in_window``, bucket into cycles (§11 cycle-bucketing DRY),
       collapse each bucket (§10 stage 1) with the per-cycle maintenance flag.
    4. ``streak(verdicts)`` → if ``None``, NOOP (nothing to reason about).
       ``anti_flap(streak, thresholds)`` → if no proposed_status, NOOP.
    5. ``component_repo.get(component_id)`` → if ``None``, NOOP + warn
       (unseeded component; no current_status to compare against — §8 step 5).
    6. Delegate to ``decide_service.decide(...)`` → return action.

    This function is **pure wiring**: it performs no domain reasoning of its
    own beyond routing to the services above. The commit-first guarantee
    (T1.1) lives inside ``DecideService``; this function does not repeat it.

    **Best-effort publish (T1.1):** the recovery-publish branch of ``decide``
    calls ``publisher.publish`` directly and lets a failure propagate. So the
    ``decide_service`` injected here MUST be wired with a best-effort publisher
    (``composition.publish_helper.BestEffortPublisher``) so a Statuspage outage
    is logged and swallowed rather than crashing the pull cycle (AC3). The DB
    write is already committed before the publish, so swallowing loses nothing.

    Args:
        signal_key: The canonical signal key (dossier §7).
        config: The loaded app config aggregate.
        observation_repo: Read path for persisted observations.
        maintenance_repo: Maintenance window lookup.
        component_repo: Component status read (``get`` by id).
        decide_service: Proposal/reconciliation service (§12 / §10 stage 4).
        clock: Injected time source (keeps the function testable).

    Returns:
        The ``DecideAction`` returned by ``DecideService.decide``, or
        ``DecideAction.NOOP`` when there is nothing to decide.
    """
    # ── 1. Config resolution ────────────────────────────────────────────────
    component_id = config.component_for_signal(signal_key)
    thresholds = config.thresholds_for(component_id)
    signal_cfg = config.signal(signal_key)
    interval = timedelta(seconds=signal_cfg.interval_seconds)

    # ── 2. Observation window (§8 step 5 / §10 window math) ─────────────────
    until = clock.now()
    max_threshold = max(
        thresholds.major, thresholds.partial, thresholds.degraded, thresholds.recovery
    )
    since = until - (max_threshold + 2) * interval

    # ── 3. Bucket into cycles → collapse (§10 stage 1 / §11 cycle-bucketing) ─
    raw_obs = list(observation_repo.in_window(signal_key, since, until))
    buckets = bucket_into_cycles(raw_obs, since=since, interval=interval)

    verdicts = [
        collapse(
            buckets[cycle_start],
            under_maintenance=maintenance_repo.is_under_maintenance(
                component_id, cycle_start
            ),
        )
        for cycle_start in sorted(buckets)
    ]

    # ── 4. Streak + anti-flap (§10 stages 2-3) ──────────────────────────────
    s = streak(verdicts)
    if s is None:
        _log.debug(
            "orchestrate_signal(%s): streak is None (no non-maintenance cycles) → NOOP",
            signal_key,
        )
        return DecideAction.NOOP

    outcome = anti_flap(s, thresholds)
    if outcome.proposed_status is None:
        if outcome.internal_warning:
            _log.debug(
                "orchestrate_signal(%s): anti_flap internal warning (streak=%d, health=%s) → NOOP",
                signal_key,
                s.length,
                s.health,
            )
        else:
            _log.debug(
                "orchestrate_signal(%s): anti_flap no proposal (streak=%d, health=%s) → NOOP",
                signal_key,
                s.length,
                s.health,
            )
        return DecideAction.NOOP

    # ── 5. Current component status (§8 step 5 / §12 reconciliation) ─────────
    current = component_repo.get(component_id)
    if current is None:
        _log.warning(
            "orchestrate_signal(%s): component %r not found in repository — "
            "skipping decide (unseeded component has no current_status). "
            "Seed the component or wait for the next topology sync.",
            signal_key,
            component_id,
        )
        return DecideAction.NOOP

    # ── 6. Decide (§12 / §10 stage 4 — commit-first lives in DecideService) ──
    return decide_service.decide(
        component_id=component_id,
        proposed_status=outcome.proposed_status,
        current_status=current.status,
        now=until,
    )
