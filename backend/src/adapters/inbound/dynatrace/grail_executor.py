"""Dynatrace Grail DQL HTTP Executor (dossier §8).

Provides the real HTTP executor for fetching synthetic monitor observations
from Dynatrace Grail storage via DQL.
"""

from __future__ import annotations

import time
from collections.abc import Callable

import httpx

from src.adapters.inbound.dynatrace.query import Executor


class GrailQueryError(RuntimeError):
    """Raised when a DQL query execution against Dynatrace Grail fails (non-2xx response)."""


def make_grail_executor(
    *,
    env_url: str,
    api_token: str,
    http_post: Callable = httpx.post,
    http_get: Callable = httpx.get,
    poll_attempts: int = 30,
    sleep_func: Callable = time.sleep,
) -> Executor:
    """Factory to create a Grail DQL executor closure (dossier §8).

    Accepts an optional `http_post`, `http_get`, and `sleep_func` seam to
    facilitate unit testing without making live HTTP calls or sleeping.
    """
    execute_endpoint = f"{env_url.rstrip('/')}/platform/storage/query/v1/query:execute"
    poll_endpoint = f"{env_url.rstrip('/')}/platform/storage/query/v1/query:poll"
    headers = {
        "Authorization": f"Api-Token {api_token}",
        "Content-Type": "application/json",
    }

    def _extract_records(data: dict) -> list[dict]:
        if (
            "result" in data
            and isinstance(data["result"], dict)
            and "records" in data["result"]
        ):
            return data["result"]["records"]
        return data.get("records", [])

    def executor(query: str) -> list[dict]:
        body = {"query": query}
        try:
            resp = http_post(execute_endpoint, headers=headers, json=body)
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

        # Sync fallback
        if resp.status_code == 200 and (
            "records" in data
            or (
                "result" in data
                and isinstance(data["result"], dict)
                and "records" in data["result"]
            )
        ):
            return _extract_records(data)

        # Handle async execution
        token = data.get("requestToken")
        if not token:
            if resp.status_code == 202:
                raise GrailQueryError(
                    "Grail returned 202 but no requestToken was provided."
                )
            return []

        # Poll loop
        for attempt in range(poll_attempts):
            if attempt > 0:
                sleep_func(0.1)

            try:
                poll_resp = http_get(
                    poll_endpoint,
                    headers=headers,
                    params={"request-token": token},
                )
            except Exception as exc:
                raise GrailQueryError(f"Grail poll request failed: {exc}") from exc

            if poll_resp.status_code < 200 or poll_resp.status_code >= 300:
                excerpt = poll_resp.text[:200]
                raise GrailQueryError(
                    f"Grail poll failed with status {poll_resp.status_code}. Response: {excerpt!r}"
                )

            try:
                poll_data = poll_resp.json()
            except ValueError as exc:
                raise GrailQueryError(
                    f"Failed to parse Grail poll JSON response: {exc}"
                ) from exc

            state = poll_data.get("state")
            if state == "SUCCEEDED":
                return _extract_records(poll_data)
            elif state in ("FAILED", "CANCELLED"):
                message = poll_data.get("message", "No message provided")
                raise GrailQueryError(
                    f"Grail query execution failed with state {state}. Message: {message}"
                )
            elif state in ("RUNNING", "NOT_STARTED"):
                continue
            else:
                raise GrailQueryError(f"Grail query returned unknown state: {state}")

        raise GrailQueryError(
            f"Grail query polling exhausted after {poll_attempts} attempts."
        )

    return executor
