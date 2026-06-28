"""Dynatrace Grail DQL HTTP Executor (dossier §8).

Provides the real HTTP executor for fetching synthetic monitor observations
from Dynatrace Grail storage via DQL.
"""

from __future__ import annotations

from collections.abc import Callable

import httpx

from src.adapters.inbound.dynatrace.query import Executor


class GrailQueryError(RuntimeError):
    """Raised when a DQL query execution against Dynatrace Grail fails (non-2xx response)."""


def make_grail_executor(
    *, env_url: str, api_token: str, http_post: Callable = httpx.post
) -> Executor:
    """Factory to create a Grail DQL executor closure (dossier §8).

    Accepts an optional `http_post` seam to facilitate unit testing without
    making live HTTP calls.
    """
    endpoint = f"{env_url.rstrip('/')}/platform/storage/query/v1/query:execute"
    headers = {
        "Authorization": f"Api-Token {api_token}",
        "Content-Type": "application/json",
    }

    def executor(query: str) -> list[dict]:
        body = {"query": query}
        try:
            resp = http_post(endpoint, headers=headers, json=body)
        except Exception as exc:
            raise GrailQueryError(f"HTTP request to Grail failed: {exc}") from exc

        if resp.status_code < 200 or resp.status_code >= 300:
            excerpt = resp.text[:200]
            raise GrailQueryError(
                f"Grail query failed with status {resp.status_code}. Response: {excerpt!r}"
            )

        try:
            data = resp.json()
        except ValueError as exc:
            raise GrailQueryError(
                f"Failed to parse Grail JSON response: {exc}"
            ) from exc

        return data.get("records", [])

    return executor
