"""Statuspage HTTP Executor implementation (dossier §6, §12).

Provides the real HTTP executor for publishing component status updates to the
Statuspage API.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx

from src.adapters.outbound.statuspage import Executor


class StatuspageApiError(RuntimeError):
    """Raised when an API call against Statuspage fails (non-2xx response)."""


def make_statuspage_executor(*, http_request: Callable = httpx.request) -> Executor:
    """Factory to create a Statuspage HTTP executor closure (dossier §6, §12).

    Accepts an optional `http_request` seam to facilitate unit testing without
    making live HTTP calls.
    """

    def executor(
        method: str, url: str, headers: dict[str, str], json_body: dict
    ) -> dict:
        try:
            resp = http_request(method, url, headers=headers, json=json_body)
        except Exception as exc:
            raise StatuspageApiError(
                f"HTTP request to Statuspage failed: {exc}"
            ) from exc

        if resp.status_code < 200 or resp.status_code >= 300:
            excerpt = resp.text[:200]
            raise StatuspageApiError(
                f"Statuspage API call failed with status {resp.status_code}. Response: {excerpt!r}"
            )

        if not resp.text.strip():
            return {}

        try:
            return resp.json()
        except ValueError as exc:
            raise StatuspageApiError(
                f"Failed to parse Statuspage JSON response: {exc}"
            ) from exc

    return executor
