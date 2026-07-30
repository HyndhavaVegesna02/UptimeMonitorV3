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

from datetime import datetime, timedelta, timezone

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


class _FakeClock:
    """A settable/advanceable clock for retention tests (STORY-183 AC1/AC4).

    AC1 forbids sleeping in real time; this lets a test move the server's
    notion of "now" forward explicitly between requests instead.
    """

    def __init__(self, start: datetime) -> None:
        self._instant = start

    def __call__(self) -> datetime:
        return self._instant

    def advance(self, delta: timedelta) -> None:
        self._instant += delta


def _execute(server: DemoEngineServer, query: str) -> str:
    resp = httpx.post(
        f"{server.base_url}/platform/storage/query/v1/query:execute",
        headers=_headers(),
        json={"query": query},
    )
    return resp.json()["requestToken"]


def _poll(server: DemoEngineServer, token: str) -> httpx.Response:
    return httpx.get(
        f"{server.base_url}/platform/storage/query/v1/query:poll",
        headers=_headers(),
        params={"request-token": token},
    )


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


def test_repeat_poll_inside_retention_returns_the_same_records_twice():
    """STORY-183 AC2: replaces STORY-180's
    `test_results_cache_is_evicted_after_being_polled`, whose contract
    (consume-on-first-poll) is the opposite of this one. That test's own
    docstring attributed the consume semantics to "STORY-180 AC4 (minor 5)",
    not to STORY-148's wire contract (AC5) -- so restoring repeat-poll
    fidelity here is the correction STORY-183 AC2 mandates, not a
    wire-contract change AC5 forbids. Real Grail serves a completed result to
    a repeat poll of the same `request-token` within its retention window;
    this asserts exactly that, with the default (5-minute) retention, well
    inside which a same-process test always completes.
    """
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        execute_resp = httpx.post(
            f"{server.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            json={"query": query},
        )
        token = execute_resp.json()["requestToken"]
        assert token in server._httpd.results

        first_poll = httpx.get(
            f"{server.base_url}/platform/storage/query/v1/query:poll",
            headers=_headers(),
            params={"request-token": token},
        )
        second_poll = httpx.get(
            f"{server.base_url}/platform/storage/query/v1/query:poll",
            headers=_headers(),
            params={"request-token": token},
        )

        assert first_poll.status_code == 200
        assert second_poll.status_code == 200
        assert first_poll.json()["state"] == "SUCCEEDED"
        assert second_poll.json()["state"] == "SUCCEEDED"
        assert first_poll.json()["records"] == second_poll.json()["records"]
        assert token in server._httpd.results


def test_entry_never_polled_is_evicted_once_past_retention():
    """STORY-183 AC1: the abandoned-token leak (a query executed and never
    polled -- e.g. a failed poll leg, `grail_executor.py:110-111`, or a
    faulted cycle the pull loop swallows, `pull_loop.py:200-207`) must not
    survive past retention. Uses an injected clock advanced past retention
    (never real-time sleep); eviction is lazy, so a second request is what
    triggers the sweep that collects the first, never-polled token.
    """
    clock = _FakeClock(datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc))
    store = DemoRowStore()
    with DemoEngineServer(
        store, retention=timedelta(seconds=30), clock=clock
    ) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        abandoned_token = _execute(server, query)
        assert abandoned_token in server._httpd.results

        clock.advance(timedelta(seconds=31))
        _execute(server, query)  # any request sweeps; this one never polls it

        assert abandoned_token not in server._httpd.results


def test_poll_after_retention_eviction_still_404s():
    """STORY-183 AC3: unchanged from today -- a poll of a token evicted by
    retention returns the same 404 body as an unknown token.
    """
    clock = _FakeClock(datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc))
    store = DemoRowStore()
    with DemoEngineServer(
        store, retention=timedelta(seconds=30), clock=clock
    ) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        token = _execute(server, query)

        clock.advance(timedelta(seconds=31))
        _execute(server, query)  # sweeps the first token

        resp = _poll(server, token)
        assert resp.status_code == 404
        assert resp.json() == {"error": "unknown request token"}


def test_cache_length_stays_bounded_when_nothing_is_polled():
    """STORY-183 AC4: the bound is asserted, not asserted-about. Drives N
    executes with the injected clock advanced PAST retention between each
    one and NO polls at all. With a stopped clock (or lazy eviction alone,
    with nothing ever triggering a sweep past the just-inserted entry) this
    would pass vacuously at `len <= N`; advancing between every execute means
    each new execute's sweep must have already collected the previous entry,
    so the length must stay strictly below N -- here, exactly 1.
    """
    clock = _FakeClock(datetime(2026, 7, 30, 12, 0, 0, tzinfo=timezone.utc))
    store = DemoRowStore()
    retention = timedelta(seconds=30)
    with DemoEngineServer(store, retention=retention, clock=clock) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        n = 5
        for _ in range(n):
            clock.advance(retention + timedelta(seconds=1))
            _execute(server, query)

        assert len(server._httpd.results) == 1
        assert len(server._httpd.results) < n


def test_unauthenticated_poll_does_not_touch_the_cache():
    """STORY-183 AC5: auth is checked BEFORE the cache is touched
    (`server.py:112` before the eviction sweep / lookup at `:124`), so an
    unauthenticated poll can never affect cache state -- neither evicting an
    unrelated entry nor (previously) consuming the one it named.
    """
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        query = build_dql_query(native_id="MON-A", watermark=None, overlap=timedelta(0))
        token = _execute(server, query)

        unauthenticated = httpx.get(
            f"{server.base_url}/platform/storage/query/v1/query:poll",
            params={"request-token": token},
        )

        assert unauthenticated.status_code == 401
        assert token in server._httpd.results

        authenticated = _poll(server, token)
        assert authenticated.status_code == 200


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


def test_malformed_json_body_returns_400():
    """A malformed request body must not escape `do_POST` as an unhandled
    `JSONDecodeError` (a stdlib traceback + a connectionless disconnect) —
    it gets the same 400-with-JSON-error-body treatment as every other bad
    input this server rejects.
    """
    store = DemoRowStore()
    with DemoEngineServer(store) as server:
        resp = httpx.post(
            f"{server.base_url}/platform/storage/query/v1/query:execute",
            headers=_headers(),
            content=b"{not valid json",
        )
        assert resp.status_code == 400
        assert "error" in resp.json()
