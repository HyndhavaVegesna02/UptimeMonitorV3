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


import json
from pathlib import Path


def _load_fixture(name: str) -> dict:
    path = Path(__file__).resolve().parent / "fixtures" / "statuspage" / f"{name}.json"
    with path.open() as f:
        return json.load(f)


def test_publisher_publishes_status_change_correctly():
    from src.core.domain.status import StatusChange, ComponentStatus
    from src.adapters.outbound.statuspage import StatuspagePublisher

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
    assert json_body == {
        "component": {
            "status": "operational"
        }
    }


def test_publisher_raises_on_unmapped_component_id():
    from src.core.domain.status import StatusChange, ComponentStatus
    from src.adapters.outbound.statuspage import StatuspagePublisher, UnmappedComponentIdError

    def fake_executor(method: str, url: str, headers: dict, json_body: dict) -> dict:
        return {}

    publisher = StatuspagePublisher(
        page_id="page-123",
        api_token="token-abc",
        component_mapping={"checkout": "comp-123"},
        executor=fake_executor,
    )

    change = StatusChange(component_id="unknown_comp", status=ComponentStatus.OPERATIONAL)
    with pytest.raises(UnmappedComponentIdError) as exc_info:
        publisher.publish(change)

    assert "unknown_comp" in str(exc_info.value)


