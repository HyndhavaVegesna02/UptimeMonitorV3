"""Tests for the Dynatrace Grail DQL HTTP Executor (dossier §8)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from src.adapters.inbound.dynatrace.dispatch import normalize_rows
from src.adapters.inbound.dynatrace.grail_executor import (
    GrailQueryError,
    make_grail_executor,
)

_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "dynatrace" / "grail_http_response.json"
)


def test_grail_executor_success():
    """Verify that a successful DQL fetch parses headers/URL and returns the row dicts."""
    recorded_body = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))

    def fake_post(url, headers, json):
        assert (
            url
            == "https://abc12345.live.dynatrace.com/platform/storage/query/v1/query:execute"
        )
        assert headers == {
            "Authorization": "Api-Token dt0c01.sampletoken",
            "Content-Type": "application/json",
        }
        assert json == {"query": "fetch dt.synthetic.executions"}
        return httpx.Response(200, json=recorded_body)

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.sampletoken",
        http_post=fake_post,
    )

    records = executor("fetch dt.synthetic.executions")
    assert len(records) == 1
    assert records[0]["event.id"] == "evt-1"

    # Verify that the records can be parsed by existing normalizers
    observations = normalize_rows(records, signal_key="checkout-http")
    assert len(observations) == 1
    assert observations[0].signal_key == "checkout-http"
    assert observations[0].location == "us-east-1"


def test_grail_executor_non_2xx_raises_error():
    """Verify that a non-2xx status code raises GrailQueryError."""

    def fake_post(url, headers, json):
        return httpx.Response(401, text="Unauthorized API Token")

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.badtoken",
        http_post=fake_post,
    )

    with pytest.raises(GrailQueryError) as exc_info:
        executor("fetch dt.synthetic.executions")

    assert "401" in str(exc_info.value)
    assert "Unauthorized API Token" in str(exc_info.value)


def test_grail_executor_empty_records_returns_empty_list():
    """Verify that absent/empty records key returns an empty list (empty-input agreement)."""

    def fake_post(url, headers, json):
        return httpx.Response(200, json={})

    executor = make_grail_executor(
        env_url="https://abc12345.live.dynatrace.com",
        api_token="dt0c01.token",
        http_post=fake_post,
    )

    records = executor("fetch dt.synthetic.executions")
    assert records == []
