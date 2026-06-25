"""STORY-008: the Dynatrace inbound adapter (dossier §5, §7, §8).

Exercises `src.adapters.inbound.dynatrace` against recorded/representative DQL
response fixtures only (`backend/tests/fixtures/dynatrace/`) — no live
Dynatrace in any test (working agreement: pure core, mockable edges).
"""

import src.adapters.inbound.dynatrace as dynatrace_adapter


def test_package_imports():
    assert dynatrace_adapter is not None
