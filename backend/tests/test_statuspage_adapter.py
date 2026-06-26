"""STORY-013: Statuspage publish adapter tests."""

import pytest
from src.adapters.outbound.statuspage import StatuspagePublisher, Executor


def test_publisher_can_be_imported():
    # Scaffolding test to watch import fail, then succeed.
    assert StatuspagePublisher is not None
    assert Executor is not None


def test_map_component_status_exhaustive():
    from src.core.domain import ComponentStatus
    from src.adapters.outbound.statuspage import map_component_status

    assert map_component_status(ComponentStatus.OPERATIONAL) == "operational"
    assert map_component_status(ComponentStatus.DEGRADED) == "degraded_performance"
    assert map_component_status(ComponentStatus.PARTIAL_OUTAGE) == "partial_outage"
    assert map_component_status(ComponentStatus.MAJOR_OUTAGE) == "major_outage"


def test_map_component_status_unknown_raises():
    from src.adapters.outbound.statuspage import map_component_status, UnknownComponentStatusError

    with pytest.raises(UnknownComponentStatusError):
        map_component_status("on_fire")

