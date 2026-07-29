"""STORY-148 AC7 — proven through the REAL executor, not a fake.

Drives `make_grail_executor` (`adapters/inbound/dynatrace/grail_executor.py`)
— completely unmodified, using its real default `httpx.post`/`httpx.get` —
against the running demo server, and asserts assembled `SignalObservation`s
come back correct through the real dispatch/normalizer/assembler chain too.
This is the specific thing option (b) buys over a fake `Executor` callable
(D4), so it is asserted here rather than assumed.
"""

from datetime import timedelta

from demo_engine.rows import build_row
from demo_engine.server import DemoEngineServer
from demo_engine.store import DemoRowStore
from src.adapters.inbound.dynatrace.dispatch import normalize_rows
from src.adapters.inbound.dynatrace.grail_executor import make_grail_executor
from src.adapters.inbound.dynatrace.query import build_dql_query
from src.core.domain import Health


def test_real_grail_executor_round_trips_a_demo_row_into_a_signal_observation():
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="HTTP_CHECK-DEMO0001",
            location="SYNTHETIC_LOCATION-DEMO0001",
            event_id="9001",
            timestamp="2026-07-29T10:00:00.000000000Z",
            duration_ms=755,
            response_status_code=200,
        )
    )

    with DemoEngineServer(store) as server:
        # make_grail_executor's own defaults (httpx.post/httpx.get) hit the
        # real socket the server owns - no fake/injected http_post/http_get.
        executor = make_grail_executor(
            env_url=server.base_url, api_token="dt0c01.demo-token"
        )

        query = build_dql_query(
            native_id="HTTP_CHECK-DEMO0001", watermark=None, overlap=timedelta(0)
        )
        rows = executor(query)

        observations = normalize_rows(rows, signal_key="demo-signal")

    assert len(observations) == 1
    observation = observations[0]
    assert observation.signal_key == "demo-signal"
    assert observation.health == Health.UP
    assert observation.source_event_id == "9001"
    assert observation.source.native_id == "HTTP_CHECK-DEMO0001"
    assert observation.location == "SYNTHETIC_LOCATION-DEMO0001"
    assert observation.latency_ms == 755
    assert observation.response_status_code == 200


def test_real_grail_executor_returns_multiple_locations_in_order():
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="HTTP_CHECK-DEMO0001",
            location="SYNTHETIC_LOCATION-A",
            event_id="1",
            timestamp="2026-07-29T10:00:00.000000000Z",
        )
    )
    store.add_row(
        build_row(
            monitor_id="HTTP_CHECK-DEMO0001",
            location="SYNTHETIC_LOCATION-B",
            event_id="2",
            timestamp="2026-07-29T10:01:00.000000000Z",
        )
    )

    with DemoEngineServer(store) as server:
        executor = make_grail_executor(
            env_url=server.base_url, api_token="dt0c01.demo-token"
        )
        query = build_dql_query(
            native_id="HTTP_CHECK-DEMO0001", watermark=None, overlap=timedelta(0)
        )
        rows = executor(query)
        observations = normalize_rows(rows, signal_key="demo-signal")

    assert [obs.location for obs in observations] == [
        "SYNTHETIC_LOCATION-A",
        "SYNTHETIC_LOCATION-B",
    ]
    assert all(obs.health == Health.UP for obs in observations)
