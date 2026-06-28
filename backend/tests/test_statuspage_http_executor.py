"""Tests for the Statuspage HTTP Executor (dossier §6, §12)."""

from __future__ import annotations

import httpx
import pytest
from src.adapters.outbound.statuspage.http_executor import (
    StatuspageApiError,
    make_statuspage_executor,
)


def test_statuspage_executor_success():
    """Verify that a successful Statuspage call forwards parameters and returns JSON."""
    recorded_response = {"id": "comp-1", "status": "operational"}

    def fake_request(method, url, headers, json):
        assert method == "PATCH"
        assert url == "https://api.statuspage.io/v1/pages/page-1/components/comp-1"
        assert headers == {"Authorization": "OAuth token123"}
        assert json == {"component": {"status": "operational"}}
        return httpx.Response(200, json=recorded_response)

    executor = make_statuspage_executor(http_request=fake_request)
    result = executor(
        "PATCH",
        "https://api.statuspage.io/v1/pages/page-1/components/comp-1",
        {"Authorization": "OAuth token123"},
        {"component": {"status": "operational"}},
    )

    assert result == recorded_response


def test_statuspage_executor_non_2xx_raises_error():
    """Verify that a non-2xx status code raises StatuspageApiError."""

    def fake_request(method, url, headers, json):
        return httpx.Response(400, text="Bad Request Parameter")

    executor = make_statuspage_executor(http_request=fake_request)

    with pytest.raises(StatuspageApiError) as exc_info:
        executor("PATCH", "https://api.statuspage.io", {}, {})

    assert "400" in str(exc_info.value)
    assert "Bad Request Parameter" in str(exc_info.value)


def test_statuspage_executor_empty_body_returns_empty_dict():
    """Verify that an empty response body returns an empty dict."""

    def fake_request(method, url, headers, json):
        return httpx.Response(204, text="")

    executor = make_statuspage_executor(http_request=fake_request)
    result = executor("PATCH", "https://api.statuspage.io", {}, {})
    assert result == {}
