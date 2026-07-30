"""HTTP server implementing the Grail wire protocol (STORY-148 AC6).

Serves exactly what `make_grail_executor` speaks
(`adapters/inbound/dynatrace/grail_executor.py:43-97`): POST
`.../platform/storage/query/v1/query:execute` -> `202` + a JSON body
carrying `requestToken` (the ASYNC branch, deliberately — a sync-only server
would only exercise the executor's fallback branch, undercutting D4's stated
reason for building a real server instead of a fake `Executor`), then GET
`.../platform/storage/query/v1/query:poll?request-token=...` ->
`state: "SUCCEEDED"` + `records` on the first poll (this engine resolves
every query synchronously server-side; only the WIRE PROTOCOL is
asynchronous — there is nothing here to actually wait on).

Three obligations `grail_executor.py` depends on, each pinned by a test in
`backend/tests/demo_engine/test_server.py`:
(a) the `202` response body is JSON (`grail_executor.py:73` parses it
    unconditionally);
(b) every poll response carries `state` (a bare `{"records": ...}` raises
    "unknown state: None", `grail_executor.py:136-137`);
(c) the `Authorization: Api-Token ...` header is required.

The per-token result cache (`_DemoHTTPServer.results`) is bounded by
RETENTION, not by consume-on-first-poll (STORY-183, replacing STORY-180
AC4/minor 5's `pop`-on-poll bound). A `pop`-based bound left an abandoned
token (a query that is executed but never successfully polled, e.g. a failed
poll leg -- `grail_executor.py:110-111` -- or the pull loop swallowing a
faulted cycle, `pull_loop.py:200-207`) cached for the process lifetime, and
it made a repeat poll of the same token 404 -- real Grail retains a completed
result and re-serves it within a retention window instead. Retention fixes
both: an entry is evicted once older than `_DEFAULT_RETENTION`, whether or
not it was ever polled, and a repeat poll inside the window returns the same
records every time.
"""

from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from demo_engine.store import DemoRowStore

_EXECUTE_PATH = "/platform/storage/query/v1/query:execute"
_POLL_PATH = "/platform/storage/query/v1/query:poll"

#: Real Grail retains a completed result for a bounded window and re-serves
#: it to a repeat poll of the same `request-token` within that window
#: (STORY-183 AC2) rather than consuming it on first read, and it does not
#: retain forever (STORY-183 AC1: an abandoned token must not leak for the
#: process lifetime). Five minutes is comfortably longer than any interval
#: this repo's own demo fleet declares (`config/demo/*.yaml`, 30-60s) or any
#: gap between an `execute` and its `poll` in the real client
#: (`grail_executor.py` polls in a tight retry loop immediately after
#: `execute`), so a normal poll always lands inside it, while still being
#: finite.
_DEFAULT_RETENTION = timedelta(minutes=5)


def _real_clock() -> datetime:
    return datetime.now(timezone.utc)


class _DemoHTTPServer(ThreadingHTTPServer):
    """A `ThreadingHTTPServer` carrying the demo store + pending results.

    The store and the per-token result cache live on the server instance
    (not the handler, whose `__init__` signature is fixed by the stdlib) so
    every request handler instance can reach them via `self.server`.

    `retention` and `clock` are genuinely per-instance (constructor
    arguments assigned directly, never copied from a module constant at
    construction time), so a caller sets them by passing them in and reads
    the EFFECTIVE value back via `self.retention` -- not by monkeypatching
    `_DEFAULT_RETENTION`, which a server that already copied it would not
    observe. `clock` defaults to the real wall clock but is read fresh on
    every use (never cached), mirroring `DemoRowStore.handle_query`'s own
    `request_instant` convention (`store.py:36-47`), so tests can inject an
    advanceable fake instead of sleeping in real time (STORY-183 AC1).
    """

    def __init__(
        self,
        address: tuple[str, int],
        store: DemoRowStore,
        *,
        retention: timedelta = _DEFAULT_RETENTION,
        clock: Callable[[], datetime] = _real_clock,
    ) -> None:
        super().__init__(address, _DemoRequestHandler)
        self.store = store
        self.retention = retention
        self._clock = clock
        self.results: dict[str, tuple[datetime, list[dict]]] = {}
        self._results_lock = threading.Lock()

    def _evict_expired(self, *, now: datetime) -> None:
        """Remove every entry older than `self.retention`.

        Takes `_results_lock` for the whole read-then-delete so a sweep
        never races a handler thread inserting a new entry mid-iteration
        (`_DemoHTTPServer` extends `ThreadingHTTPServer` over a bare dict;
        STORY-182 drives up to 41 concurrent signal loops through this
        server). Called from both `do_POST` and `do_GET` so the abandoned-
        token path (Problem 1, never polled at all) is swept even if nothing
        ever polls again.
        """
        with self._results_lock:
            expired_tokens = [
                token
                for token, (inserted_at, _records) in self.results.items()
                if now - inserted_at > self.retention
            ]
            for token in expired_tokens:
                del self.results[token]


class _DemoRequestHandler(BaseHTTPRequestHandler):
    server: _DemoHTTPServer  # narrows the stdlib `BaseServer` type for callers

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        pass  # keep test output quiet; nothing here signals a test failure

    def _write_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _require_auth(self) -> bool:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Api-Token "):
            self._write_json(
                401, {"error": "missing or malformed Authorization header"}
            )
            return False
        return True

    def do_POST(self) -> None:  # noqa: N802 - stdlib method name
        # Drain the request body BEFORE any early return (404/401): closing
        # the connection with unread bytes still sitting in the socket's
        # receive buffer can make the OS send a TCP RST instead of a clean
        # close, which shows up to the client as an intermittent
        # `ConnectionResetError`/`httpx.ReadError` (reproduced live on
        # Windows against the 401 branch when the body went unread).
        length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(length) if length else b"{}"

        if urlsplit(self.path).path != _EXECUTE_PATH:
            self._write_json(404, {"error": "not found"})
            return
        if not self._require_auth():
            return

        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError as exc:
            self._write_json(400, {"error": f"malformed JSON body: {exc}"})
            return
        query = body.get("query", "")

        try:
            records = self.server.store.handle_query(query)
        except Exception as exc:
            self._write_json(400, {"error": str(exc)})
            return

        # Sweep BEFORE inserting the new entry: this is the only place an
        # abandoned token (Problem 1 -- never polled at all) can ever be
        # collected, since nothing here polls proactively.
        now = self.server._clock()
        self.server._evict_expired(now=now)
        token = uuid.uuid4().hex
        with self.server._results_lock:
            self.server.results[token] = (now, records)
        self._write_json(202, {"requestToken": token})

    def do_GET(self) -> None:  # noqa: N802 - stdlib method name
        split = urlsplit(self.path)
        if split.path != _POLL_PATH:
            self._write_json(404, {"error": "not found"})
            return
        if not self._require_auth():
            return

        params = parse_qs(split.query)
        token = params.get("request-token", [None])[0]
        # Read, not popped (STORY-183 AC2): a token inside the retention
        # window is served to EVERY poll, not just the first -- real Grail
        # retains a completed result and re-serves it. The auth check above
        # runs before this line, so an unauthenticated poll never reaches
        # the cache (AC5).
        now = self.server._clock()
        self.server._evict_expired(now=now)
        with self.server._results_lock:
            entry = self.server.results.get(token) if token else None
        if entry is None:
            self._write_json(404, {"error": "unknown request token"})
            return

        _inserted_at, records = entry
        self._write_json(200, {"state": "SUCCEEDED", "records": records})


class DemoEngineServer:
    """Owns the server socket + background thread for the life of a `with` block.

    Binds to port 0 by default and reads the ACTUALLY bound port back off
    the live socket (`server_address`) via `base_url` — never a port number
    computed and handed off before/after the bind (the exact defect class
    STORY-179 hit in this repo's own DynamoDB-Local test fixture).

    `retention` and `clock` pass straight through to `_DemoHTTPServer`
    (STORY-183): a caller (a test, or a reality-gate harness) sets the
    cache's effective retention by constructing with `retention=...` and
    reads it back via `server._httpd.retention` -- never by monkeypatching
    `_DEFAULT_RETENTION`, which a running instance has already copied and
    would not observe. Pass a settable fake for `clock` (e.g. a small
    callable object with an `advance()` method) to move time forward without
    sleeping in real time.
    """

    def __init__(
        self,
        store: DemoRowStore,
        *,
        host: str = "127.0.0.1",
        port: int = 0,
        retention: timedelta = _DEFAULT_RETENTION,
        clock: Callable[[], datetime] = _real_clock,
    ) -> None:
        self._httpd = _DemoHTTPServer(
            (host, port), store, retention=retention, clock=clock
        )
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}"

    def __enter__(self) -> "DemoEngineServer":
        self._thread.start()
        return self

    def __exit__(self, *exc_info: object) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        self._thread.join(timeout=5)
