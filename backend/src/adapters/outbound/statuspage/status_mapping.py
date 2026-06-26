"""Status mapping for Statuspage outbound adapter (dossier §6, §12)."""

from src.core.domain import ComponentStatus

_STATUS_MAP = {
    ComponentStatus.OPERATIONAL: "operational",
    ComponentStatus.DEGRADED: "degraded_performance",
    ComponentStatus.PARTIAL_OUTAGE: "partial_outage",
    ComponentStatus.MAJOR_OUTAGE: "major_outage",
}


class UnknownComponentStatusError(ValueError):
    """Raised when a component status is not one of the mapped Statuspage states."""


def map_component_status(status: ComponentStatus) -> str:
    """Translate a canonical ComponentStatus to a Statuspage component status string.

    Raises UnknownComponentStatusError if the status is unrecognized.
    """
    try:
        return _STATUS_MAP[status]
    except KeyError:
        raise UnknownComponentStatusError(
            f"unknown ComponentStatus: {status!r}"
        ) from None
