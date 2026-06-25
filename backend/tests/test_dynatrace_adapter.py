"""STORY-008: the Dynatrace inbound adapter (dossier §5, §7, §8).

Exercises `src.adapters.inbound.dynatrace` against recorded/representative DQL
response fixtures only (`backend/tests/fixtures/dynatrace/`) — no live
Dynatrace in any test (working agreement: pure core, mockable edges).
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

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


# --- Step 5: HTTP health mapping success/failure/partial -> up/down/degraded ---


def test_health_mapping_is_explicit_for_success_failure_partial():
    from src.adapters.inbound.dynatrace.health_mapping import map_execution_outcome

    assert map_execution_outcome("success") is Health.UP
    assert map_execution_outcome("failure") is Health.DOWN
    assert map_execution_outcome("partial") is Health.DEGRADED


def test_health_mapping_rejects_unknown_outcome():
    from src.adapters.inbound.dynatrace.health_mapping import (
        UnknownVendorOutcomeError,
        map_execution_outcome,
    )

    with pytest.raises(UnknownVendorOutcomeError):
        map_execution_outcome("timeout")


def test_http_normalizer_maps_success_failure_partial_rows_across_locations():
    from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row

    rows = _load("http_multi_location.json")["records"]

    success_obs = normalize_http_row(rows[0], signal_key="checkout-http")
    failure_obs = normalize_http_row(rows[1], signal_key="checkout-http")
    partial_obs = normalize_http_row(rows[2], signal_key="checkout-http")

    assert success_obs.health is Health.UP
    assert success_obs.location == "us-east-1"

    assert failure_obs.health is Health.DOWN
    assert failure_obs.location == "eu-west-1"
    assert failure_obs.latency_ms is None

    assert partial_obs.health is Health.DEGRADED
    assert partial_obs.location == "ap-southeast-1"
    assert partial_obs.latency_ms == 980


# --- Step 6: clickpath normalizer collapses multi-step to ONE verdict ---------


def test_clickpath_normalizer_collapses_multi_step_row_to_one_verdict():
    from src.adapters.inbound.dynatrace.clickpath_normalizer import (
        normalize_clickpath_row,
    )

    rows = _load("clickpath_multi_location.json")["records"]
    success_row = rows[0]  # us-east-1, all 3 steps succeed

    obs = normalize_clickpath_row(success_row, signal_key="sockshop-purchase")

    assert obs.signal_key == "sockshop-purchase"
    assert obs.observed_at == datetime(2026, 6, 24, 10, 5, 0, tzinfo=timezone.utc)
    assert obs.health is Health.UP  # one monitor-level verdict, not 3 step verdicts
    assert obs.source_event_id == "evt-clickpath-journey-001"
    assert obs.source.system == "dynatrace"
    assert obs.source.native_id == "CLICKPATH-7B3C"
    assert obs.source.native_kind == "clickpath"
    assert obs.location == "us-east-1"
    assert obs.latency_ms == 2310
    # Step detail is not modelled on the canonical shape at all.
    assert not hasattr(obs, "steps")


def test_clickpath_normalizer_one_failed_step_yields_monitor_level_down():
    from src.adapters.inbound.dynatrace.clickpath_normalizer import (
        normalize_clickpath_row,
    )

    rows = _load("clickpath_multi_location.json")["records"]
    failure_row = rows[1]  # eu-west-1, checkout step fails

    obs = normalize_clickpath_row(failure_row, signal_key="sockshop-purchase")

    assert obs.health is Health.DOWN
    assert obs.location == "eu-west-1"
    assert obs.latency_ms is None


def test_clickpath_normalizer_can_attach_raw_ref_without_core_reading_steps():
    from src.adapters.inbound.dynatrace.clickpath_normalizer import (
        normalize_clickpath_row,
    )

    rows = _load("clickpath_multi_location.json")["records"]
    obs = normalize_clickpath_row(
        rows[0], signal_key="sockshop-purchase", raw_ref="s3://raw/evt-clickpath-journey-001.json"
    )

    assert obs.raw_ref == "s3://raw/evt-clickpath-journey-001.json"


# --- Step 7: adapter dispatch -> flat list, one obs per location execution ----


def test_dispatch_normalizes_mixed_monitor_types_to_flat_observation_list():
    from src.adapters.inbound.dynatrace.dispatch import normalize_rows

    rows = _load("mixed_monitor_types.json")["records"]

    observations = normalize_rows(rows, signal_key="sockshop-mixed")

    assert len(observations) == 2  # one per row/location execution, no aggregation
    assert {obs.source.native_kind for obs in observations} == {"http", "clickpath"}

    http_obs = next(o for o in observations if o.source.native_kind == "http")
    clickpath_obs = next(o for o in observations if o.source.native_kind == "clickpath")

    assert http_obs.source_event_id == "evt-mixed-http-001"
    assert http_obs.health is Health.UP
    assert http_obs.location == "us-east-1"

    assert clickpath_obs.source_event_id == "evt-mixed-clickpath-001"
    assert clickpath_obs.health is Health.UP
    assert clickpath_obs.location == "us-east-1"


def test_dispatch_produces_one_observation_per_row_no_aggregation():
    from src.adapters.inbound.dynatrace.dispatch import normalize_rows

    rows = _load("http_multi_location.json")["records"]  # 3 distinct locations

    observations = normalize_rows(rows, signal_key="checkout-http")

    assert len(observations) == 3
    assert {obs.location for obs in observations} == {
        "us-east-1",
        "eu-west-1",
        "ap-southeast-1",
    }


# --- Step 8: out-of-scope monitor type surfaced as unsupported (AC5) ----------


def test_dispatch_raises_unsupported_for_single_browser_monitor_type():
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_row,
    )

    rows = _load("unsupported_monitor_type.json")["records"]
    browser_row = rows[0]  # synthetic_test.type == "BROWSER" (single-browser)

    with pytest.raises(UnsupportedMonitorTypeError):
        normalize_row(browser_row, signal_key="homepage-browser")


def test_dispatch_raises_unsupported_for_nam_monitor_type():
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_row,
    )

    rows = _load("unsupported_monitor_type.json")["records"]
    nam_row = rows[1]  # synthetic_test.type == "NAM"

    with pytest.raises(UnsupportedMonitorTypeError):
        normalize_row(nam_row, signal_key="nam-check")


def test_normalize_rows_raises_unsupported_rather_than_mis_normalizing():
    """A batch mixing a supported row with an unsupported one must raise, not
    silently drop or mis-normalize the unsupported row as HTTP/clickpath.
    """
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_rows,
    )

    supported_row = _load("http_multi_location.json")["records"][0]
    unsupported_row = _load("unsupported_monitor_type.json")["records"][0]

    with pytest.raises(UnsupportedMonitorTypeError):
        normalize_rows([supported_row, unsupported_row], signal_key="mixed-scope")


# --- Step 9: DQL query builder (watermark + overlap window) + injected executor


def test_build_query_scopes_to_monitor_id_and_newer_than_watermark_minus_overlap():
    from src.adapters.inbound.dynatrace.query import build_dql_query

    watermark = datetime(2026, 6, 24, 10, 0, 0, tzinfo=timezone.utc)
    overlap = timedelta(minutes=5)

    query = build_dql_query(
        native_id="HTTP_CHECK-9F2A", watermark=watermark, overlap=overlap
    )

    assert "HTTP_CHECK-9F2A" in query
    # The query reads from (watermark - overlap) = 10:00 - 5min = 09:55, never
    # from the bare watermark, so a slow-to-land row just before the cursor is
    # never missed (dossier §8).
    assert "2026-06-24T09:55:00" in query
    assert "2026-06-24T10:00:00" not in query


def test_build_query_with_no_watermark_has_no_lower_time_bound():
    from src.adapters.inbound.dynatrace.query import build_dql_query

    query = build_dql_query(
        native_id="HTTP_CHECK-9F2A", watermark=None, overlap=timedelta(minutes=5)
    )

    assert "HTTP_CHECK-9F2A" in query
    assert "timestamp >=" not in query


def test_build_query_rejects_naive_watermark():
    from src.adapters.inbound.dynatrace.query import build_dql_query

    naive = datetime(2026, 6, 24, 10, 0, 0)

    with pytest.raises(ValueError):
        build_dql_query(
            native_id="HTTP_CHECK-9F2A", watermark=naive, overlap=timedelta(minutes=5)
        )


def test_fetch_observations_uses_injected_executor_and_normalizes_rows():
    """The live executor is a thin injected seam — never called live in tests.

    A fake executor stands in for the real DQL HTTP call and returns the
    recorded HTTP fixture rows; `fetch_observations` must build a query (via
    the injected executor's input), call the executor exactly once, and
    normalize every returned row.
    """
    from src.adapters.inbound.dynatrace.adapter import fetch_observations

    rows = _load("http_multi_location.json")["records"]
    calls = []

    def fake_executor(query: str) -> list[dict]:
        calls.append(query)
        return rows

    observations = fetch_observations(
        signal_key="checkout-http",
        native_id="HTTP_CHECK-9F2A",
        watermark=None,
        executor=fake_executor,
    )

    assert len(calls) == 1
    assert "HTTP_CHECK-9F2A" in calls[0]
    assert len(observations) == 3
    assert all(obs.signal_key == "checkout-http" for obs in observations)
    assert {obs.location for obs in observations} == {
        "us-east-1",
        "eu-west-1",
        "ap-southeast-1",
    }


def test_fetch_observations_raises_unsupported_for_unsupported_monitor_rows():
    from src.adapters.inbound.dynatrace.adapter import fetch_observations
    from src.adapters.inbound.dynatrace.dispatch import UnsupportedMonitorTypeError

    rows = _load("unsupported_monitor_type.json")["records"]

    def fake_executor(query: str) -> list[dict]:
        return rows

    with pytest.raises(UnsupportedMonitorTypeError):
        fetch_observations(
            signal_key="homepage-browser",
            native_id="BROWSER-4D1E",
            watermark=None,
            executor=fake_executor,
        )
