"""Core logic pipeline, stage 4 (dossier §10 decide + §12 reconciliation) — pure core.

`decide` is the final pipeline stage: it takes anti-flap's proposed
`ComponentStatus` (stage 3, `core/services/pipeline.py`) and turns it into the
right side effect against the component's CURRENT PUBLISHED status, reconciling
any open proposal as it goes. It makes TWO comparisons (dossier §10 + §12):

  - **vs the current published status (§10)** decides what to *publish*: a
    proposal worse than current is a degradation that goes through the human
    gate (nothing auto-publishes); a proposal better than current is a recovery
    that auto-publishes (recoveries need no approval); same publishes nothing.
  - **vs the open proposal (§12 "the reconciliation rule")** decides what
    happens to the pending proposal so the human always sees exactly one — the
    current worst: a worse computed status SUPERSEDES the lesser open proposal
    and a new one is created; a recovered status OBSOLETES the pending
    degradation with *nothing published* (the customer was never shown the
    outage, so there is nothing to clear — this closes the V2 stale-approval
    bug); the same status leaves it untouched.

The two never conflict: a published degradation has no open proposal (it was
approved, hence terminal), so the "obsolete the pending" and "publish a
recovery" branches are mutually exclusive in practice.

`current_status` is INJECTED (the component's `components.status`, supplied by
the composition layer / first end-to-end thread) — never read here — keeping
this stage pure, mirroring `collapse`'s `under_maintenance` and `anti_flap`'s
`thresholds`. All repository writes are committed BEFORE the best-effort
publish (commit-first), so a publish failure never loses the recorded decision.

This module imports ONLY `src.core.*` — no SQL, no vendor types, no I/O. The
two ports are injected via the constructor so the service is fully exercisable
with in-memory fakes (no DB, no Statuspage).
"""

from datetime import datetime
from enum import Enum

from src.core.domain import ComponentStatus, StatusChange, ProposalState, StatusProposal
from src.core.domain.status import is_worse, severity_rank
from src.core.ports import ProposalRepository, StatusPublisherPort


class DecideAction(str, Enum):
    """The primary outcome of one `decide` call, for logging and assertions.

    A single-field marker (no cross-field invariant, so no validator needed):
    `NOOP` (nothing changed), `PROPOSED` (a new degradation proposal was
    opened), `SUPERSEDED` (a lesser open proposal was superseded and a worse
    one opened), `OBSOLETED` (a pending degradation was obsoleted on recovery),
    `PUBLISHED_RECOVERY` (a recovery that improved the published status was
    auto-published). The pull loop (STORY-016) logs this; tests assert on it.
    """

    NOOP = "noop"
    PROPOSED = "proposed"
    SUPERSEDED = "superseded"
    OBSOLETED = "obsoleted"
    PUBLISHED_RECOVERY = "published_recovery"


class DecideService:
    """Pipeline stage 4: reconcile a proposed status into proposals + publishes (dossier §10, §12).

    Constructed with the two core ports the stage depends on — no globals, no
    SQL: `ProposalRepository` for the §12 reconciliation
    (`get_open`/`create_open`/`resolve`) and `StatusPublisherPort` for the §10
    recovery auto-publish. See the module docstring for the two-comparison rule.
    """

    def __init__(
        self,
        *,
        proposal_repo: ProposalRepository,
        publisher: StatusPublisherPort,
    ) -> None:
        self._proposal_repo = proposal_repo
        self._publisher = publisher

    def decide(
        self,
        *,
        component_id: str,
        proposed_status: ComponentStatus,
        current_status: ComponentStatus,
        now: datetime,
        reason: str | None = None,
    ) -> DecideAction:
        """Apply the §10 publish rule + §12 reconciliation for one component (commit-first).

        Compares `proposed_status` (from anti-flap) to the component's
        `current_status` (the injected current published status) and to the
        single open proposal, if any:

        - **worse than current** (a degradation, the human gate): with no open
          proposal, open one (`PROPOSED`); with an open proposal of a different
          status, `resolve` it `SUPERSEDED` and open the new worst
          (`SUPERSEDED`); with an identical open proposal, leave it (`NOOP`).
          Nothing is published — degradations wait for approval.
        - **better than current** (a recovery): publish the recovery via the
          `StatusPublisherPort` (`PUBLISHED_RECOVERY`); recoveries are not
          gated.
        - **recovered while a degradation is pending** (proposed not worse than
          current, but an open proposal exists): `resolve` it `OBSOLETED` with
          `nothing published` (§12) — the outage was never shown
          (`OBSOLETED`).
        - **same with nothing pending**: `NOOP`.

        Repository writes happen BEFORE the publish, so a publishing failure
        propagates AFTER the decision is durably recorded (commit-first; no
        rollback). `create_open` returning `None` (the partial-unique safety
        net — a concurrent open exists) degrades to `NOOP` rather than crashing.
        """
        opened = self._proposal_repo.get_open(component_id)
        proposed_is_degradation = is_worse(proposed_status, current_status)
        proposed_is_better = severity_rank(proposed_status) < severity_rank(current_status)

        publish_change = None
        action = DecideAction.NOOP

        if proposed_is_better:
            publish_change = StatusChange(component_id=component_id, status=proposed_status)
            action = DecideAction.PUBLISHED_RECOVERY

        if proposed_is_degradation:
            if opened is None:
                prop = StatusProposal(
                    component_id=component_id,
                    from_status=current_status,
                    to_status=proposed_status,
                    state=ProposalState.OPEN,
                    proposed_at=now,
                )
                persisted = self._proposal_repo.create_open(prop)
                if persisted is None:
                    action = DecideAction.NOOP
                else:
                    action = DecideAction.PROPOSED
            elif opened.to_status != proposed_status:
                self._proposal_repo.resolve(
                    opened.id,
                    to_state=ProposalState.SUPERSEDED,
                    reason=reason,
                    resolved_at=now,
                )
                prop = StatusProposal(
                    component_id=component_id,
                    from_status=current_status,
                    to_status=proposed_status,
                    state=ProposalState.OPEN,
                    proposed_at=now,
                )
                persisted = self._proposal_repo.create_open(prop)
                if persisted is None:
                    action = DecideAction.NOOP
                else:
                    action = DecideAction.SUPERSEDED
            else:
                # open.to_status == proposed_status -> leave it
                action = DecideAction.NOOP
        else:
            # proposed is operational-or-equal vs published -> no human gate
            if opened is not None:
                self._proposal_repo.resolve(
                    opened.id,
                    to_state=ProposalState.OBSOLETED,
                    reason=reason,
                    resolved_at=now,
                )
                action = DecideAction.OBSOLETED

        if publish_change is not None:
            self._publisher.publish(publish_change)

        return action



