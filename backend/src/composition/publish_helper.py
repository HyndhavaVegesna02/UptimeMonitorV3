"""Publish composition helpers (dossier §12, §14 T1.1)."""

import logging

from src.core.domain.status import StatusChange
from src.core.ports import StatusPublisherPort


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
