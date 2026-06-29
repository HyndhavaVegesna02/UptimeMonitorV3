"""STORY-016b: the Dynatrace inbound adapter (dossier §5, §7, §8).

Exercises `src.adapters.inbound.dynatrace` against recorded/representative DQL
response fixtures only (`backend/tests/fixtures/dynatrace/`) — no live
Dynatrace in any test (working agreement: pure core, mockable edges).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import src.adapters.inbound.dynatrace as dynatrace_adapter
from src.core.domain import Health

_FIXTURES = Path(__file__).parent / "fixtures" / "dynatrace"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text())


def _enrich_clickpath(row: dict) -> dict:
    r = row.copy()
    r.setdefault("dt.synthetic.monitor.id", "CLICKPATH-7B3C")
    r.setdefault(
        "dt.entity.synthetic_location",
        r.get("synthetic_location.name") or "us-east-1",
    )
    r.setdefault("event.type", "BROWSER_CLICKPATH")
    r.setdefault("event.id", "evt-clickpath-journey-001")
    r.setdefault("timestamp", "2026-06-24T10:05:00.000000000Z")
    return r


def test_package_imports():
    assert dynatrace_adapter is not None


# --- HTTP normalizer maps one row -> canonical SignalObservation -----


def test_http_normalizer_maps_one_location_execution_row():
    from src.adapters.inbound.dynatrace.http_normalizer import normalize_http_row

    rows = _load("grail_synthetic_events.json")["records"]
    row = rows[0]  # TodoMVC Homepage Monitor, HEALTHY/0

    obs = normalize_http_row(row, signal_key="checkout-http")

    assert obs.signal_key == "checkout-http"
    assert obs.observed_at == datetime(
        2026, 6, 29, 6, 45, 40, 742000, tzinfo=timezone.utc
    )
    assert obs.observed_at.tzinfo is not None
    assert obs.health is Health.UP
    assert obs.source_event_id == "156340723200"
    assert obs.source.system == "dynatrace"
    assert obs.source.native_id == "HTTP_CHECK-DB5792CB88D14CF4"
    assert obs.source.native_kind == "http"
    assert obs.location == "SYNTHETIC_LOCATION-000000000000005C"
    assert obs.latency_ms == 787


# --- HTTP health mapping success/failure/partial -> up/down/degraded ---


def test_health_mapping_is_explicit_for_success_failure_partial():
    from src.adapters.inbound.dynatrace.health_mapping import (
        map_execution_outcome,
    )

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


def test_health_mapping_synthetic_status_success():
    from src.adapters.inbound.dynatrace.health_mapping import (
        map_synthetic_status,
    )

    assert map_synthetic_status(code="0", message="HEALTHY") is Health.UP
    assert map_synthetic_status(code="123", message="HEALTHY") is Health.UP


def test_health_mapping_synthetic_status_rejects_unknown():
    from src.adapters.inbound.dynatrace.health_mapping import (
        UnknownVendorStatusError,
        map_synthetic_status,
    )

    with pytest.raises(UnknownVendorStatusError) as exc_info:
        map_synthetic_status(code="-1", message="UNRECOGNIZED_OUTCOME")
    assert "code='-1'" in str(exc_info.value)
    assert "message='UNRECOGNIZED_OUTCOME'" in str(exc_info.value)


# --- clickpath normalizer collapses multi-step to ONE verdict ---------


def test_clickpath_normalizer_collapses_multi_step_row_to_one_verdict():
    from src.adapters.inbound.dynatrace.clickpath_normalizer import (
        normalize_clickpath_row,
    )

    rows = _load("clickpath_multi_location.json")["records"]
    success_row = _enrich_clickpath(rows[0])
    obs = normalize_clickpath_row(success_row, signal_key="sockshop-purchase")

    assert obs.signal_key == "sockshop-purchase"
    assert obs.health is Health.UP
    assert obs.source_event_id == "evt-clickpath-journey-001"
    assert obs.source.system == "dynatrace"
    assert obs.source.native_kind == "clickpath"


def test_clickpath_normalizer_one_failed_step_yields_monitor_level_down():
    from src.adapters.inbound.dynatrace.clickpath_normalizer import (
        normalize_clickpath_row,
    )

    rows = _load("clickpath_multi_location.json")["records"]
    failure_row = _enrich_clickpath(rows[1])
    obs = normalize_clickpath_row(failure_row, signal_key="sockshop-purchase")

    assert obs.health is Health.DOWN
    assert obs.location == "eu-west-1"


def test_clickpath_normalizer_can_attach_raw_ref_without_core_reading_steps():
    from src.adapters.inbound.dynatrace.clickpath_normalizer import (
        normalize_clickpath_row,
    )

    rows = _load("clickpath_multi_location.json")["records"]
    obs = normalize_clickpath_row(
        _enrich_clickpath(rows[0]),
        signal_key="sockshop-purchase",
        raw_ref="s3://raw/evt-clickpath-journey-001.json",
    )

    assert obs.raw_ref == "s3://raw/evt-clickpath-journey-001.json"


# --- normalizer dispatch (routes DQL rows to their correct normalizer) --


def test_dispatch_normalizes_to_flat_observation_list():
    from src.adapters.inbound.dynatrace.dispatch import normalize_rows

    rows = _load("grail_synthetic_events.json")["records"]
    observations = normalize_rows(rows, signal_key="checkout-http")

    assert len(observations) == 2
    assert all(obs.health is Health.UP for obs in observations)
    assert observations[0].source_event_id == "156340723200"
    assert observations[1].source_event_id == "156340723201"


# --- out-of-scope monitor type surfaced as unsupported (AC5) ----------


def test_dispatch_raises_unsupported_for_single_browser_monitor_type():
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_row,
    )

    rows = _load("unsupported_monitor_type.json")["records"]
    browser_row = rows[0]  # event.type == "BROWSER" (single-browser)

    with pytest.raises(UnsupportedMonitorTypeError):
        normalize_row(browser_row, signal_key="homepage-browser")


def test_dispatch_raises_unsupported_for_nam_monitor_type():
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_row,
    )

    rows = _load("unsupported_monitor_type.json")["records"]
    nam_row = rows[1]  # event.type == "NAM"

    with pytest.raises(UnsupportedMonitorTypeError):
        normalize_row(nam_row, signal_key="nam-check")


def test_normalize_rows_raises_unsupported_rather_than_mis_normalizing():
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
        normalize_rows,
    )

    supported_row = _load("grail_synthetic_events.json")["records"][0]
    unsupported_row = _load("unsupported_monitor_type.json")["records"][0]

    with pytest.raises(UnsupportedMonitorTypeError):
        normalize_rows([supported_row, unsupported_row], signal_key="mixed-scope")


# --- STORY-020: malformed DQL row -> named error, not bare KeyError -----------


def test_dispatch_raises_malformed_for_missing_event_type():
    from src.adapters.inbound.dynatrace.dispatch import (
        MalformedDqlRowError,
        normalize_row,
    )

    row = _load("grail_synthetic_events.json")["records"][0].copy()
    del row["event.type"]

    with pytest.raises(MalformedDqlRowError, match="event.type"):
        normalize_row(row, signal_key="checkout-http")


@pytest.mark.parametrize(
    "missing_field",
    [
        "timestamp",
        "event.id",
        "dt.synthetic.monitor.id",
        "dt.entity.synthetic_location",
    ],
)
def test_assemble_observation_raises_malformed_for_missing_required_field(
    missing_field,
):
    from src.adapters.inbound.dynatrace._assembly import (
        MalformedDqlRowError,
        assemble_observation,
    )

    row = _load("grail_synthetic_events.json")["records"][0].copy()
    del row[missing_field]

    with pytest.raises(MalformedDqlRowError, match=re.escape(missing_field)):
        assemble_observation(
            row,
            signal_key="checkout-http",
            health=Health.UP,
            native_kind="http",
        )


def test_assemble_observation_does_not_require_optional_latency():
    from src.adapters.inbound.dynatrace._assembly import assemble_observation

    row = _load("grail_synthetic_events.json")["records"][0].copy()
    del row["result.statistics.duration"]

    obs = assemble_observation(
        row, signal_key="checkout-http", health=Health.UP, native_kind="http"
    )
    assert obs.latency_ms is None


# --- fetch_observations integration test ---


def test_fetch_observations_uses_injected_executor_and_normalizes_rows():
    from src.adapters.inbound.dynatrace.adapter import fetch_observations

    rows = _load("grail_synthetic_events.json")["records"]
    calls = []

    def fake_executor(query: str) -> list[dict]:
        calls.append(query)
        return rows

    observations = fetch_observations(
        signal_key="checkout-http",
        native_id="HTTP_CHECK-DB5792CB88D14CF4",
        watermark=None,
        executor=fake_executor,
    )

    assert len(calls) == 1
    assert "HTTP_CHECK-DB5792CB88D14CF4" in calls[0]
    assert len(observations) == 2
    assert all(obs.signal_key == "checkout-http" for obs in observations)


def test_fetch_observations_raises_unsupported_for_unsupported_monitor_rows():
    from src.adapters.inbound.dynatrace.adapter import fetch_observations
    from src.adapters.inbound.dynatrace.dispatch import (
        UnsupportedMonitorTypeError,
    )

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


# --- Fix loop 1: shared assembly helper ---


def test_assemble_observation_builds_canonical_shape_from_a_bare_row():
    from src.adapters.inbound.dynatrace._assembly import assemble_observation

    rows = _load("grail_synthetic_events.json")["records"]
    row = rows[0]

    obs = assemble_observation(
        row, signal_key="checkout-http", health=Health.UP, native_kind="http"
    )

    assert obs.signal_key == "checkout-http"
    assert obs.observed_at == datetime(
        2026, 6, 29, 6, 45, 40, 742000, tzinfo=timezone.utc
    )
    assert obs.health is Health.UP
    assert obs.source_event_id == "156340723200"
    assert obs.source.native_id == "HTTP_CHECK-DB5792CB88D14CF4"
    assert obs.source.native_kind == "http"
    assert obs.location == "SYNTHETIC_LOCATION-000000000000005C"
    assert obs.latency_ms == 787
    assert obs.raw_ref is None


# --- build_dql_query: real Grail schema (AC1, STORY-016b) ---


def test_build_dql_query_targets_real_object_and_filter_field():
    from src.adapters.inbound.dynatrace.query import build_dql_query

    q = build_dql_query(
        native_id="HTTP_CHECK-DB5792CB88D14CF4",
        watermark=None,
        overlap=timedelta(minutes=5),
    )
    # AC1: the real data object + the real filter field.
    assert "fetch dt.synthetic.events" in q
    assert 'dt.synthetic.monitor.id == "HTTP_CHECK-DB5792CB88D14CF4"' in q
    # The retired placeholder names must be gone.
    assert "dt.synthetic.executions" not in q
    assert "synthetic_test.id" not in q
    # No watermark -> no lower time bound.
    assert "timestamp >=" not in q


def test_build_dql_query_with_watermark_adds_overlap_lower_bound():
    from src.adapters.inbound.dynatrace.query import build_dql_query

    watermark = datetime(2026, 6, 29, 6, 0, 0, tzinfo=timezone.utc)
    q = build_dql_query(
        native_id="HTTP_CHECK-DB5792CB88D14CF4",
        watermark=watermark,
        overlap=timedelta(minutes=5),
    )
    # since = watermark - overlap = 05:55:00Z (never the bare watermark).
    assert 'timestamp >= "2026-06-29T05:55:00Z"' in q


def test_build_dql_query_rejects_naive_watermark():
    from src.adapters.inbound.dynatrace.query import build_dql_query

    with pytest.raises(ValueError, match="tz-aware UTC"):
        build_dql_query(
            native_id="HTTP_CHECK-DB5792CB88D14CF4",
            watermark=datetime(2026, 6, 29, 6, 0, 0),  # naive
            overlap=timedelta(minutes=5),
        )


def test_build_dql_query_rejects_native_id_with_dql_breaking_char():
    from src.adapters.inbound.dynatrace.query import (
        InvalidNativeIdError,
        build_dql_query,
    )

    with pytest.raises(InvalidNativeIdError):
        build_dql_query(
            native_id='HTTP_CHECK-"; drop',  # contains a quote
            watermark=None,
            overlap=timedelta(minutes=5),
        )


# --- parse_ns_timestamp edge cases (precision-boundary, STORY-016b) ---


def test_parse_ns_timestamp_truncates_nanoseconds_to_microseconds():
    from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp

    # 9 fractional digits -> µs (6 digits); fromisoformat would otherwise reject it.
    assert parse_ns_timestamp("2026-06-29T06:45:40.742000000Z") == datetime(
        2026, 6, 29, 6, 45, 40, 742000, tzinfo=timezone.utc
    )


def test_parse_ns_timestamp_handles_no_fractional_and_explicit_offset():
    from src.adapters.inbound.dynatrace._assembly import parse_ns_timestamp

    # No fractional part, Z suffix.
    assert parse_ns_timestamp("2026-06-29T06:45:40Z") == datetime(
        2026, 6, 29, 6, 45, 40, tzinfo=timezone.utc
    )
    # Explicit +00:00 offset with ns fractional.
    assert parse_ns_timestamp("2026-06-29T06:45:40.742000000+00:00") == datetime(
        2026, 6, 29, 6, 45, 40, 742000, tzinfo=timezone.utc
    )


def test_assemble_observation_attaches_optional_raw_ref():
    from src.adapters.inbound.dynatrace._assembly import assemble_observation

    rows = _load("clickpath_multi_location.json")["records"]
    row = _enrich_clickpath(rows[0])

    obs = assemble_observation(
        row,
        signal_key="sockshop-purchase",
        health=Health.UP,
        native_kind="clickpath",
        raw_ref="s3://raw/evt-clickpath-journey-001.json",
    )

    assert obs.raw_ref == "s3://raw/evt-clickpath-journey-001.json"
