"""STORY-070: live vendor-id drift health check (composition zone, dossier §8).

During the Sprint 38 review a configured Dynatrace monitor `native_id` had
been silently recreated in Dynatrace (a new id), so the pull loop kept
polling the STALE id every cycle (HTTP 200, correctly formed query) and
ingested nothing for 30 days -- a "trusted-and-wrong" no-data pipeline (fixed
by hotfix 79bfbb3). This module proves the startup drift probe: for each
configured signal, a bounded DQL count query is run through the injected
`Executor` seam (never a live Dynatrace call, working agreement) and a 0-row/
0-count result produces a LOUD WARNING naming the monitor; a healthy id stays
quiet; and an executor that raises is caught + logged, never propagated (the
probe must not block live-loop startup, decided sprint-41 planning).
"""

from __future__ import annotations

import logging

from src.composition.config import AppConfig, ComponentConfig, Config, SignalConfig
from src.composition.vendor_health import build_vendor_health_query, check_vendor_id_health


def _one_signal_config(*, native_id: str = "HTTP_CHECK-DEAD", signal_key: str = "sig-1") -> Config:
    return Config(
        [
            AppConfig(
                id="app-1",
                name="App 1",
                monitor_provider="dynatrace",
                components=[ComponentConfig(id="comp-1", name="Comp 1")],
                signals=[
                    SignalConfig(
                        signal_key=signal_key,
                        native_id=native_id,
                        name="Signal 1",
                        component_id="comp-1",
                        interval_seconds=30,
                    )
                ],
            )
        ]
    )


def _two_signal_config() -> Config:
    return Config(
        [
            AppConfig(
                id="app-1",
                name="App 1",
                monitor_provider="dynatrace",
                components=[ComponentConfig(id="comp-1", name="Comp 1")],
                signals=[
                    SignalConfig(
                        signal_key="sig-dead",
                        native_id="HTTP_CHECK-DEAD",
                        name="Dead Signal",
                        component_id="comp-1",
                        interval_seconds=30,
                    ),
                    SignalConfig(
                        signal_key="sig-alive",
                        native_id="HTTP_CHECK-ALIVE",
                        name="Alive Signal",
                        component_id="comp-1",
                        interval_seconds=30,
                    ),
                ],
            )
        ]
    )


def test_build_vendor_health_query_scopes_to_native_id_and_bounded_window():
    """The query fetches a bounded window, filters on the monitor id, and
    summarizes a count -- never the full ingest fetch shape (no watermark/
    overlap/event.type scoping; this is a cheap existence probe, not ingest).
    """
    query = build_vendor_health_query(native_id="HTTP_CHECK-ABC123")

    assert 'dt.synthetic.monitor.id == "HTTP_CHECK-ABC123"' in query
    assert "summarize count()" in query
    assert "fetch dt.synthetic.events" in query
    assert "from:now()-" in query


def test_zero_rows_logs_loud_warning_naming_the_monitor(caplog):
    """AC1: a configured native_id that returns 0 rows over the check window
    produces a LOUD, testable WARNING naming the monitor (not a silent no-op).
    """
    config = _one_signal_config(native_id="HTTP_CHECK-DB5792CB88D14CF4", signal_key="httpcheck")

    def fake_executor(query: str) -> list[dict]:
        return []

    with caplog.at_level(logging.WARNING):
        check_vendor_id_health(config=config, executor=fake_executor)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "HTTP_CHECK-DB5792CB88D14CF4" in message
    assert "httpcheck" in message


def test_zero_count_row_also_logs_warning(caplog):
    """A `summarize count()` row present but with a count of 0 is the same
    "no live executions" signal as an empty row list -- both must warn.
    """
    config = _one_signal_config(native_id="HTTP_CHECK-DEAD", signal_key="sig-1")

    def fake_executor(query: str) -> list[dict]:
        return [{"count()": 0}]

    with caplog.at_level(logging.WARNING):
        check_vendor_id_health(config=config, executor=fake_executor)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "HTTP_CHECK-DEAD" in warnings[0].getMessage()


def test_healthy_id_logs_no_warning(caplog):
    """A monitor id with live executions in the window produces NO warning."""
    config = _one_signal_config(native_id="HTTP_CHECK-38B092E93932C002", signal_key="sig-1")

    def fake_executor(query: str) -> list[dict]:
        return [{"count()": 2882}]

    with caplog.at_level(logging.WARNING):
        check_vendor_id_health(config=config, executor=fake_executor)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert warnings == []


def test_probe_error_is_caught_logged_and_does_not_raise(caplog):
    """A probe that raises (HTTP failure, malformed response, vendor timeout)
    must be caught and logged, never propagated -- the probe must not block
    live-loop startup (decided sprint-41 planning, NOT fail-fast).
    """
    config = _one_signal_config(native_id="HTTP_CHECK-DEAD", signal_key="sig-1")

    def failing_executor(query: str) -> list[dict]:
        raise RuntimeError("Grail query failed with status 500")

    with caplog.at_level(logging.WARNING):
        # Must not raise.
        check_vendor_id_health(config=config, executor=failing_executor)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "HTTP_CHECK-DEAD" in message
    assert "sig-1" in message


def test_probe_error_on_one_signal_does_not_block_others(caplog):
    """One dead/unreachable monitor id's probe error must not prevent the
    OTHER configured signals from being probed (each signal is independent).
    """
    config = _two_signal_config()

    def selective_executor(query: str) -> list[dict]:
        if "HTTP_CHECK-DEAD" in query:
            raise RuntimeError("boom")
        return [{"count()": 100}]

    with caplog.at_level(logging.WARNING):
        check_vendor_id_health(config=config, executor=selective_executor)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    # Only the failing probe warns; the healthy signal stays quiet.
    assert len(warnings) == 1
    assert "sig-dead" in warnings[0].getMessage()


def test_multiple_signals_each_probed_independently(caplog):
    """AC1/AC2: every configured signal gets its own probe -- a mix of one
    dead and one healthy id produces exactly one warning, naming only the
    dead one.
    """
    config = _two_signal_config()

    def fake_executor(query: str) -> list[dict]:
        if "HTTP_CHECK-DEAD" in query:
            return []
        return [{"count()": 500}]

    with caplog.at_level(logging.WARNING):
        check_vendor_id_health(config=config, executor=fake_executor)

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1
    message = warnings[0].getMessage()
    assert "HTTP_CHECK-DEAD" in message
    assert "sig-dead" in message
    assert "HTTP_CHECK-ALIVE" not in message


def test_empty_config_is_a_no_op(caplog):
    """No configured signals at all -- nothing to probe, nothing logged."""
    config = Config([])

    def fake_executor(query: str) -> list[dict]:
        raise AssertionError("executor must not be called when there are no signals")

    with caplog.at_level(logging.WARNING):
        check_vendor_id_health(config=config, executor=fake_executor)

    assert caplog.records == []
