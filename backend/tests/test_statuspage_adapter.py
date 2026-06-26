"""STORY-013: Statuspage publish adapter tests."""

import pytest
from src.adapters.outbound.statuspage import StatuspagePublisher, Executor


def test_publisher_can_be_imported():
    # Scaffolding test to watch import fail, then succeed.
    assert StatuspagePublisher is not None
    assert Executor is not None
