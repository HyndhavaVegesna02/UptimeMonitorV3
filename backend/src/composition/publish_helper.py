"""Publish composition helpers (dossier §12, §14 T1.1, STORY-072).

Contains three complementary publisher decorators plus the shared chain
assembly both composition roots use:
- `BestEffortPublisher` — wraps a delegate and never lets publish failures escape.
- `RecordingPublisher` — wraps a delegate and records EVERY publish attempt
  with a `succeeded`/`failed` outcome (STORY-072), independent of whether the
  delegate itself succeeded.
- `StatusWritebackPublisher` (STORY-045, dossier §9/§12) — wraps a delegate and
  a `ComponentRepository`; writes `components.status` back FIRST, then delegates.

They compose per the STORY-045 D2 shape:
`StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(real_publisher)),
component_repo)` — the durable status write-back happens BEFORE the best-effort
external call, so a Statuspage outage never loses the write-back, while an
unknown component id (a topology/change disagreement) propagates loudly.
`build_publisher` assembles this chain (or its no-creds `LoggingPublisher`
fallback) in ONE place so `composition/run.py` and `composition/app.py` never
drift (2026-06-25 share-the-assembly agreement).
"""

import logging

from src.core.domain.publication import Publication, PublicationOutcome
from src.core.domain.status import StatusChange
from src.core.ports import StatusPublisherPort
from src.core.ports.clock import ClockPort
from src.core.ports.component_repository import ComponentRepository
from src.core.ports.publication_repository import PublicationRepository

_log = logging.getLogger(__name__)


class BestEffortPublisher(StatusPublisherPort):
    """A `StatusPublisherPort` that wraps a delegate and never lets a publish
    failure escape (dossier §14 T1.1).

    `DecideService` calls `publisher.publish(...)` directly and lets a failure
    PROPAGATE (its core contract; see `test_decide.py`). So the composition root
    that wires `DecideService` for the orchestration injects THIS wrapper, so a
    Statuspage outage on the recovery-publish path is logged and swallowed rather
    than crashing the pull cycle (STORY-016a AC3). The DB write has already been
    committed before the publish (commit-first), so swallowing here loses nothing.

    The best-effort try/except (STORY-047 AC2) lives directly here — the ONE
    canonical best-effort seam — rather than split across this class and a
    parallel free function.
    """

    def __init__(self, delegate: StatusPublisherPort) -> None:
        self._delegate = delegate

    def publish(self, change: StatusChange) -> None:
        """Publish via the delegate, logging any errors but never raising.

        Ensures a Statuspage outage never crashes or rolls back the
        already-committed decision.
        """
        try:
            self._delegate.publish(change)
        except Exception as e:
            _log.exception(
                "Failed to publish status change for %s to Statuspage: %s",
                change.component_id,
                e,
            )


class RecordingPublisher(StatusPublisherPort):
    """A `StatusPublisherPort` decorator that records EVERY publish attempt (STORY-072).

    Wraps a delegate publisher and a `PublicationRepository`. On each `publish`:
      1. Calls `delegate.publish(change)`.
      2. IF the delegate succeeds (no exception), records a `Publication` via
         `publication_repo.record(...)` with `outcome=SUCCEEDED`, using
         `clock.now()` as the timestamp.
      3. IF the delegate RAISES, records a `Publication` with
         `outcome=FAILED` FIRST, THEN re-raises the original error — so the
         attempt is durably recorded independent of the Statuspage result
         (STORY-072 AC1) even though the caller still sees the exception
         propagate (the outer `BestEffortPublisher` swallows it from there).

    Composes inside `BestEffortPublisher` (assembled live in STORY-016):
        `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))`.
    The BestEffortPublisher outer layer logs+swallows delegate failures, so a
    raising delegate leads to: error logged, a `FAILED` publication recorded,
    no crash.
    """

    def __init__(
        self,
        delegate: StatusPublisherPort,
        publication_repo: PublicationRepository,
        clock: ClockPort,
    ) -> None:
        self._delegate = delegate
        self._publication_repo = publication_repo
        self._clock = clock

    def publish(self, change: StatusChange) -> None:
        """Publish via delegate; record the attempt's outcome either way (STORY-072).

        A raising delegate is recorded with `outcome=FAILED` and then
        RE-RAISED unchanged — recording never masks or replaces the original
        error for the caller (`BestEffortPublisher`, further out, is what
        swallows it).
        """
        try:
            self._delegate.publish(change)
        except Exception:
            self._publication_repo.record(
                Publication(
                    component_id=change.component_id,
                    status=change.status,
                    published_at=self._clock.now(),
                    outcome=PublicationOutcome.FAILED,
                )
            )
            raise
        else:
            self._publication_repo.record(
                Publication(
                    component_id=change.component_id,
                    status=change.status,
                    published_at=self._clock.now(),
                    outcome=PublicationOutcome.SUCCEEDED,
                )
            )


class LoggingPublisher(StatusPublisherPort):
    """A no-op `StatusPublisherPort` that logs the status change and does nothing else (dossier §12).

    Used when Statuspage credentials are not configured in the environment.
    """

    def publish(self, change: StatusChange) -> None:
        _log.info(
            "LoggingPublisher: status change logged (Statuspage disabled): component=%s status=%s",
            change.component_id,
            change.status,
        )


class StatusWritebackPublisher(StatusPublisherPort):
    """A `StatusPublisherPort` decorator that writes back `components.status`
    BEFORE delegating (STORY-045, dossier §9, §12, §14 T1.1, D1).

    Wraps a delegate publisher and a `ComponentRepository`. On each `publish`:
      1. Calls `component_repo.set_status(change.component_id, change.status)` —
         a durable DB write, applied FIRST (commit-first, mirroring §T1.1).
      2. THEN calls `delegate.publish(change)`.

    Sits OUTSIDE `BestEffortPublisher` in the composition chain (D2): the
    write-back is a DB write and must PROPAGATE on failure (an unknown
    component id means the topology seed and the change disagree — loud,
    never swallowed) — only the external Statuspage call inside the delegate
    chain is best-effort. Because the write-back happens before the delegate
    is ever invoked, a delegate failure (swallowed further in by
    `BestEffortPublisher`) can never undo it — this is what makes both the
    approve trigger (`ApprovalService`) and the recovery trigger
    (`DecideService`) see `components.status` updated even when Statuspage is
    down or absent (the `LoggingPublisher` no-creds path included).
    """

    def __init__(
        self, delegate: StatusPublisherPort, component_repo: ComponentRepository
    ) -> None:
        self._delegate = delegate
        self._component_repo = component_repo

    def publish(self, change: StatusChange) -> None:
        """Write back the component's status, then delegate (commit-first, D1).

        Raises `ComponentNotFoundError` (propagated from
        `ComponentRepository.set_status`) if `change.component_id` is unknown —
        the delegate is never reached in that case.
        """
        self._component_repo.set_status(change.component_id, change.status)
        self._delegate.publish(change)


def build_publisher(
    *,
    component_repo: ComponentRepository,
    publication_repo: PublicationRepository,
    clock: ClockPort,
    statuspage_page_id: str | None,
    statuspage_api_token: str | None,
    component_mapping: dict[str, str],
) -> StatusPublisherPort:
    """Assemble the shared D2 publisher chain (STORY-045, dossier §12, §17).

    The ONE place both composition roots (`composition/run.py::build_live_loop`
    for the recovery-publish trigger, `composition/app.py::create_app` for the
    approve trigger) build the publisher chain, so they can never drift
    (2026-06-25 share-the-assembly agreement):

    - `statuspage_page_id`, `statuspage_api_token`, AND `component_mapping` all
      present/non-empty: `StatusWritebackPublisher(BestEffortPublisher(
      RecordingPublisher(StatuspagePublisher(...))), component_repo)`.
    - Otherwise: `StatusWritebackPublisher(LoggingPublisher(), component_repo)`
      — the write-back still applies on the no-creds local dev path (so the
      Dashboard reflects a decision even without live Statuspage credentials).

    Publication-recording semantics (STORY-072): a `publications` row is
    written on EVERY attempt via `RecordingPublisher`, carrying
    `outcome=succeeded`/`failed` — independent of whether the Statuspage call
    itself succeeds.
    """
    if statuspage_page_id and statuspage_api_token and component_mapping:
        from src.adapters.outbound.statuspage import StatuspagePublisher
        from src.adapters.outbound.statuspage.http_executor import (
            make_statuspage_executor,
        )

        statuspage_publisher = StatuspagePublisher(
            page_id=statuspage_page_id,
            api_token=statuspage_api_token,
            component_mapping=component_mapping,
            executor=make_statuspage_executor(),
        )
        recording_publisher = RecordingPublisher(
            delegate=statuspage_publisher,
            publication_repo=publication_repo,
            clock=clock,
        )
        delegate: StatusPublisherPort = BestEffortPublisher(
            delegate=recording_publisher
        )
    else:
        delegate = LoggingPublisher()

    return StatusWritebackPublisher(delegate, component_repo)
