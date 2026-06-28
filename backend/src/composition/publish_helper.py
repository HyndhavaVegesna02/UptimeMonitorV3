"""Publish composition helpers (dossier §12, §14 T1.1)."""

import logging

from src.core.domain.status import StatusChange
from src.core.ports import StatusPublisherPort

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
