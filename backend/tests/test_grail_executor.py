"""Tests for the Dynatrace Grail DQL HTTP Executor (dossier §8, STORY-016b)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from src.adapters.inbound.dynatrace.grail_executor import (
    GrailQueryError,
    make_grail_executor,
)

_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "dynatrace" / "grail_synthetic_events.json"
)


def test_grail_executor_sync_fallback():
    """Verify that a synchronous HTTP 200 response with records directly is returned immediately."""
    recorded_body = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

    def fake_post(url, headers, json):
        assert (
            url
            == "https://abc12345.live.dynatrace.com/platform/storage/query/v1/query:execute"
        )
        assert headers["Authorization"] == "Api-Token dt0c01.sampletoken"
        return httpx.Response(200, json=recorded_body)

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.sampletoken",
        http_post=fake_post,
    )

    records = executor("fetch dt.synthetic.events")
    assert len(records) == 2
    assert records[0]["event.id"] == "156345503298"


def test_grail_executor_async_polling_success():
    """Verify that a 202 response triggers polling until SUCCEEDED and returns the records (AC2)."""
    recorded_body = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

    poll_calls = []

    def fake_post(url, headers, json):
        return httpx.Response(
            202, json={"state": "RUNNING", "requestToken": "token-123"}
        )

    def fake_get(url, headers, params):
        assert (
            url
            == "https://abc12345.live.dynatrace.com/platform/storage/query/v1/query:poll"
        )
        assert headers["Authorization"] == "Api-Token dt0c01.sampletoken"
        assert params == {"request-token": "token-123"}
        poll_calls.append(params)
        if len(poll_calls) == 1:
            return httpx.Response(200, json={"state": "RUNNING"})
        return httpx.Response(200, json={"state": "SUCCEEDED", "result": recorded_body})

    sleep_calls = []

    def fake_sleep(secs):
        sleep_calls.append(secs)

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.sampletoken",
        http_post=fake_post,
        http_get=fake_get,
        sleep_func=fake_sleep,
    )

    records = executor("fetch dt.synthetic.events")
    assert len(records) == 2
    assert len(poll_calls) == 2
    assert len(sleep_calls) == 1  # slept once between attempts


def test_grail_executor_async_polling_failure_state():
    """Verify that if the query transitions to FAILED or CANCELLED state, GrailQueryError is raised."""

    def fake_post(url, headers, json):
        return httpx.Response(
            202, json={"state": "RUNNING", "requestToken": "token-123"}
        )

    def fake_get(url, headers, params):
        return httpx.Response(
            200, json={"state": "FAILED", "message": "DQL Syntax Error"}
        )

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.sampletoken",
        http_post=fake_post,
        http_get=fake_get,
        sleep_func=lambda s: None,
    )

    with pytest.raises(
        GrailQueryError, match="failed with state FAILED. Message: DQL Syntax Error"
    ):
        executor("fetch dt.synthetic.events")


def test_grail_executor_async_polling_exhaustion():
    """Verify that if polling attempts are exhausted, GrailQueryError is raised."""

    def fake_post(url, headers, json):
        return httpx.Response(
            202, json={"state": "RUNNING", "requestToken": "token-123"}
        )

    def fake_get(url, headers, params):
        return httpx.Response(200, json={"state": "RUNNING"})

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.sampletoken",
        http_post=fake_post,
        http_get=fake_get,
        poll_attempts=3,
        sleep_func=lambda s: None,
    )

    with pytest.raises(GrailQueryError, match="polling exhausted after 3 attempts"):
        executor("fetch dt.synthetic.events")


def test_grail_executor_empty_records_returns_empty_list():
    """Verify that absent/empty records key returns an empty list (empty-input agreement)."""

    def fake_post(url, headers, json):
        return httpx.Response(200, json={"records": []})

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.token",
        http_post=fake_post,
    )

    records = executor("fetch dt.synthetic.events")
    assert records == []


def test_grail_executor_non_2xx_raises_error():
    """Verify that a non-2xx status code on execute raises GrailQueryError."""

    def fake_post(url, headers, json):
        return httpx.Response(401, text="Unauthorized API Token")

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.badtoken",
        http_post=fake_post,
    )

    with pytest.raises(GrailQueryError) as exc_info:
        executor("fetch dt.synthetic.events")

    assert "401" in str(exc_info.value)
    assert "Unauthorized API Token" in str(exc_info.value)
