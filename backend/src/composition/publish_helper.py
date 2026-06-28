"""Publish composition helpers (dossier §12, §14 T1.1).

Contains two complementary publisher decorators:
- `BestEffortPublisher` — wraps a delegate and never lets publish failures escape.
- `RecordingPublisher` — wraps a delegate and records each SUCCESSFUL publish.

They compose naturally: `BestEffortPublisher(RecordingPublisher(real_publisher))`
logs+swallows on failure and records only on success, matching the §12/T1.1
commit-first/best-effort contract.
"""

import logging

from src.core.domain.publication import Publication
from src.core.domain.status import StatusChange
from src.core.ports import StatusPublisherPort
from src.core.ports.clock import ClockPort
from src.core.ports.publication_repository import PublicationRepository

_log = logging.getLogger(__name__)


def publish_best_effort(
    publisher: StatusPublisherPort,
    change: StatusChange,
    *,
    logger: logging.Logger,
) -> None:
    """Publish a status change best-effort, logging any errors but not raising.

    Ensures a Statuspage outage never crashes or rolls back the already-committed
    decision.
    """
    try:
        publisher.publish(change)
    except Exception as e:
        logger.exception(
            "Failed to publish status change for %s to Statuspage: %s",
            change.component_id,
            e,
        )


class BestEffortPublisher(StatusPublisherPort):
    """A `StatusPublisherPort` that wraps a delegate and never lets a publish
    failure escape (dossier §14 T1.1).

    `DecideService` calls `publisher.publish(...)` directly and lets a failure
    PROPAGATE (its core contract; see `test_decide.py`). So the composition root
    that wires `DecideService` for the orchestration injects THIS wrapper, so a
    Statuspage outage on the recovery-publish path is logged and swallowed rather
    than crashing the pull cycle (STORY-016a AC3). The DB write has already been
    committed before the publish (commit-first), so swallowing here loses nothing.
    """

    def __init__(self, delegate: StatusPublisherPort) -> None:
        self._delegate = delegate

    def publish(self, change: StatusChange) -> None:
        publish_best_effort(self._delegate, change, logger=_log)


class RecordingPublisher(StatusPublisherPort):
    """A `StatusPublisherPort` decorator that records each SUCCESSFUL publish.

    Wraps a delegate publisher and a `PublicationRepository`. On each `publish`:
      1. Calls `delegate.publish(change)`.
      2. IF the delegate succeeds (no exception), records a `Publication` via
         `publication_repo.record(...)` using `clock.now()` as the timestamp.
      3. If the delegate RAISES, the error propagates BEFORE any recording —
         nothing is written to the publications table (§12/T1.1: the table has
         no error column; only successful publishes are recorded).

    Composes inside `BestEffortPublisher` (assembled live in STORY-016):
        `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))`.
    The BestEffortPublisher outer layer logs+swallows delegate failures, so a
    raising delegate leads to: error logged, nothing recorded, no crash.
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
        """Publish via delegate, then record success; propagate failures without recording."""
        self._delegate.publish(change)
        # Only reached on success — errors propagate before this line.
        self._publication_repo.record(
            Publication(
                component_id=change.component_id,
                status=change.status,
                published_at=self._clock.now(),
            )
        )
