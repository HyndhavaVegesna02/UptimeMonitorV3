"""STORY-008: the Dynatrace inbound adapter (dossier §5, §7, §8).

Exercises `src.adapters.inbound.dynatrace` against recorded/representative DQL
response fixtures only (`backend/tests/fixtures/dynatrace/`) — no live
Dynatrace in any test (working agreement: pure core, mockable edges).
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import src.adapters.inbound.dynatrace as dynatrace_adapter
from src.core.domain import Health

_FIXTURES = Path(__file__).parent / "fixtures" / "dynatrace"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text())


def test_package_imports():
    assert dynatrace_adapter is not None


# --- Step 3/4: HTTP normalizer maps one row -> canonical SignalObservation -----


def test_http_normalizer_maps_one_location_execution_row():
    from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row

    rows = _load("http_multi_location.json")["records"]
    row = rows[0]  # us-east-1, success

    obs = normalize_http_row(row, signal_key="checkout-http")

    assert obs.signal_key == "checkout-http"
    assert obs.observed_at == datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    assert obs.observed_at.tzinfo is not None
    assert obs.health is Health.UP
    assert obs.source_event_id == "evt-http-checkout-001"
    assert obs.source.system == "dynatrace"
    assert obs.source.native_id == "HTTP_CHECK-9F2A"
    assert obs.source.native_kind == "http"
    assert obs.location == "us-east-1"
    assert obs.latency_ms == 142
