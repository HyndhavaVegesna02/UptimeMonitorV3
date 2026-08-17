"""STORY-013: Statuspage publish adapter tests."""

import json
from pathlib import Path

import pytest
from src.adapters.outbound.statuspage import StatuspagePublisher


def test_map_component_status_exhaustive():
    from src.adapters.outbound.statuspage import map_component_status
    from src.core.domain import ComponentStatus

    assert map_component_status(ComponentStatus.OPERATIONAL) == "operational"
    assert map_component_status(ComponentStatus.DEGRADED) == "degraded_performance"
    assert map_component_status(ComponentStatus.PARTIAL_OUTAGE) == "partial_outage"
    assert map_component_status(ComponentStatus.MAJOR_OUTAGE) == "major_outage"


def test_map_component_status_unknown_raises():
    from src.adapters.outbound.statuspage import (
        UnknownComponentStatusError,
        map_component_status,
    )

    with pytest.raises(UnknownComponentStatusError):
        map_component_status("on_fire")


def _load_fixture(name: str) -> dict:
    path = Path(__file__).resolve().parent / "fixtures" / "statuspage" / f"{name}.json"
    with path.open() as f:
        return json.load(f)


def test_publisher_publishes_status_change_correctly():
    from src.core.domain.status import ComponentStatus, StatusChange

    # STORY-147 AC4 / STORY-227 AC5: neither `group` nor `description` can
    # reach Statuspage -- structurally guaranteed, since `StatusChange`
    # (what `publish()` reads) carries only these two fields. Pinned here,
    # on the OPERATIONAL case this test already builds, rather than in a
    # near-duplicate test with a strictly weaker payload assertion (the
    # duplicate collapsed away; this pin is the only part of it that
    # mattered).
    assert set(StatusChange.model_fields) == {"component_id", "status"}

    recorded_calls = []

    def fake_executor(method: str, url: str, headers: dict, json_body: dict) -> dict:
        recorded_calls.append((method, url, headers, json_body))
        if json_body.get("component", {}).get("status") == "operational":
            return _load_fixture("component_operational")
        return _load_fixture("component_degraded")

    publisher = StatuspagePublisher(
        page_id="page-123",
        api_token="token-abc",
        component_mapping={"checkout": "comp-123"},
        executor=fake_executor,
    )

    change = StatusChange(component_id="checkout", status=ComponentStatus.OPERATIONAL)
    publisher.publish(change)

    assert len(recorded_calls) == 1
    method, url, headers, json_body = recorded_calls[0]
    assert method == "PATCH"
    assert url == "https://api.statuspage.io/v1/pages/page-123/components/comp-123"
    assert headers == {
        "Authorization": "OAuth token-abc",
        "Content-Type": "application/json",
    }
    assert json_body == {"component": {"status": "operational"}}


def test_publisher_publishes_degraded_status_change_correctly():
    from src.core.domain.status import ComponentStatus, StatusChange

    recorded_calls = []

    def fake_executor(method: str, url: str, headers: dict, json_body: dict) -> dict:
        recorded_calls.append((method, url, headers, json_body))
        return _load_fixture("component_degraded")

    publisher = StatuspagePublisher(
        page_id="page-123",
        api_token="token-abc",
        component_mapping={"checkout": "comp-123"},
        executor=fake_executor,
    )

    change = StatusChange(component_id="checkout", status=ComponentStatus.DEGRADED)
    publisher.publish(change)

    assert len(recorded_calls) == 1
    method, url, headers, json_body = recorded_calls[0]
    assert method == "PATCH"
    assert url == "https://api.statuspage.io/v1/pages/page-123/components/comp-123"
    assert headers == {
        "Authorization": "OAuth token-abc",
        "Content-Type": "application/json",
    }
    assert json_body == {"component": {"status": "degraded_performance"}}


def test_publisher_raises_on_unmapped_component_id():
    from src.adapters.outbound.statuspage import (
        UnmappedComponentIdError,
    )
    from src.core.domain.status import ComponentStatus, StatusChange

    def fake_executor(method: str, url: str, headers: dict, json_body: dict) -> dict:
        return {}

    publisher = StatuspagePublisher(
        page_id="page-123",
        api_token="token-abc",
        component_mapping={"checkout": "comp-123"},
        executor=fake_executor,
    )

    change = StatusChange(
        component_id="unknown_comp", status=ComponentStatus.OPERATIONAL
    )
    with pytest.raises(UnmappedComponentIdError) as exc_info:
        publisher.publish(change)

    assert "unknown_comp" in str(exc_info.value)


def test_best_effort_publisher_catches_and_logs_error(caplog):
    # STORY-047 AC2: publish_best_effort was folded into BestEffortPublisher
    # (one canonical best-effort seam) — exercise it via the class directly.
    import logging

    from src.composition.publish_helper import BestEffortPublisher
    from src.core.domain.status import ComponentStatus, StatusChange

    class RaisingPublisher:
        def publish(self, change: StatusChange) -> None:
            raise RuntimeError("Statuspage is down!")

    publisher = BestEffortPublisher(RaisingPublisher())
    change = StatusChange(component_id="checkout", status=ComponentStatus.DEGRADED)

    with caplog.at_level(logging.ERROR, logger="src.composition.publish_helper"):
        publisher.publish(change)

    assert len(caplog.records) == 1
    assert "Failed to publish status change for checkout to Statuspage" in caplog.text
