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
"""

from __future__ import annotations

import json
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from demo_engine.store import DemoRowStore

_EXECUTE_PATH = "/platform/storage/query/v1/query:execute"
_POLL_PATH = "/platform/storage/query/v1/query:poll"


class _DemoHTTPServer(ThreadingHTTPServer):
    """A `ThreadingHTTPServer` carrying the demo store + pending results.

    The store and the per-token result cache live on the server instance
    (not the handler, whose `__init__` signature is fixed by the stdlib) so
    every request handler instance can reach them via `self.server`.
    """

    def __init__(self, address: tuple[str, int], store: DemoRowStore) -> None:
        super().__init__(address, _DemoRequestHandler)
        self.store = store
        self.results: dict[str, list[dict]] = {}


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

        token = uuid.uuid4().hex
        self.server.results[token] = records
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
        records = self.server.results.get(token) if token else None
        if records is None:
            self._write_json(404, {"error": "unknown request token"})
            return

        self._write_json(200, {"state": "SUCCEEDED", "records": records})


class DemoEngineServer:
    """Owns the server socket + background thread for the life of a `with` block.

    Binds to port 0 by default and reads the ACTUALLY bound port back off
    the live socket (`server_address`) via `base_url` — never a port number
    computed and handed off before/after the bind (the exact defect class
    STORY-179 hit in this repo's own DynamoDB-Local test fixture).
    """

    def __init__(
        self, store: DemoRowStore, *, host: str = "127.0.0.1", port: int = 0
    ) -> None:
        self._httpd = _DemoHTTPServer((host, port), store)
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
