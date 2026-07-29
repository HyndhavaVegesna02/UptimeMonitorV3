"""STORY-148 AC6 — the HTTP protocol, pinned literally.

Drives the server with REAL HTTP calls (`httpx`, real sockets — no fakes),
proving it implements exactly what `make_grail_executor` speaks
(`grail_executor.py:43-97`): POST `.../query:execute` -> 202 + a JSON body
carrying `requestToken`, then GET `.../query:poll?request-token=...` ->
`state: "SUCCEEDED"` + `records`. The three easy-to-miss server obligations
the AC calls out are each asserted directly:

(a) the 202 body is JSON (`grail_executor.py:73` parses it unconditionally);
(b) every poll response carries `state`;
(c) the Authorization header is required (`Api-Token ...`).
"""

from datetime import timedelta

import httpx
import pytest
from demo_engine.rows import build_row
from demo_engine.server import DemoEngineServer
from demo_engine.store import DemoRowStore
from src.adapters.inbound.dynatrace.grail_executor import (
    GrailQueryError,
    make_grail_executor,
)
from src.adapters.inbound.dynatrace.query import build_dql_query
from src.composition.vendor_health import build_vendor_health_query


def _headers():
    return {"Authorization": "Api-Token dt0c01.demo-token"}


def test_execute_returns_202_with_a_json_body_carrying_a_request_token():
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        resp = httpx.post(
            f"{server.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            json={"query": query},
        )

        assert resp.status_code == 202
        body = resp.json()
        assert "requestToken" in body
        assert isinstance(body["requestToken"], str) and body["requestToken"]


def test_poll_returns_succeeded_state_and_the_matching_records():
    store = DemoRowStore()
    store.add_row(
        build_row(
            monitor_id="MON-A",
            location="LOC-1",
            event_id="1",
            timestamp="2026-07-29T10:00:00.000000000Z",
        )
    )
    with DemoEngineServer(store) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        execute_resp = httpx.post(
            f"{server.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            json={"query": query},
        )
        token = execute_resp.json()["requestToken"]

        poll_resp = httpx.get(
            f"{server.base_url}/platform/storage/query/v1/query:poll",
            headers=_headers(),
            params={"request-token": token},
        )

        assert poll_resp.status_code == 200
        poll_body = poll_resp.json()
        assert poll_body["state"] == "SUCCEEDED"
        assert [row["event.id"] for row in poll_body["records"]] == ["1"]


def test_missing_authorization_header_is_rejected():
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        resp = httpx.post(
            f"{server.base_url}/platform/storage/query/v1/query:execute",
            json={"query": "fetch dt.synthetic.events"},
        )
        assert resp.status_code == 401


def test_two_server_instances_never_collide_on_a_hardcoded_port():
    """Each server binds port 0 and reads back the ACTUALLY bound port
    (never an ephemeral port picked and handed off separately) — the exact
    port-safety rule this story's own environment note exists to enforce.
    """
    store_one = DemoRowStore()
    store_two = DemoRowStore()
    with (
        DemoEngineServer(store_one) as server_one,
        DemoEngineServer(store_two) as server_two,
    ):
        assert server_one.base_url != server_two.base_url

        health_query = build_vendor_health_query(native_id="MON-A")
        resp_one = httpx.post(
            f"{server_one.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            json={"query": health_query},
        )
        resp_two = httpx.post(
            f"{server_two.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            json={"query": health_query},
        )
        assert resp_one.status_code == 202
        assert resp_two.status_code == 202


def test_unrecognized_query_returns_400():
    """A query matching neither DQL grammar must surface as an HTTP 400, not
    a 202 carrying an empty/garbage result — the loud-not-silent contract
    `query_grammar.py` promises, exercised over the real wire protocol.
    """
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        resp = httpx.post(
            f"{server.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            json={"query": "fetch dt.synthetic.events"},
        )
        assert resp.status_code == 400


def test_unrecognized_query_makes_the_real_grail_executor_raise_not_return_empty():
    """The client-side consequence that pins "loud, not silent": driven
    through the REAL, unmodified `make_grail_executor`, a 400 from an
    unrecognized query must raise `GrailQueryError` — never come back as `[]`
    (`grail_executor.py:97`'s silent-empty branch, which is exactly what a
    wrong query would look like as "no data" if this ever regressed).
    """
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        executor = make_grail_executor(
            env_url=server.base_url, api_token="dt0c01.demo-token"
        )
        with pytest.raises(GrailQueryError):
            executor("fetch dt.synthetic.events")
