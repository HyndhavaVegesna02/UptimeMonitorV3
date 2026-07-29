# Grail-shaped demo engine (STORY-148, part 1 of 2)

A local HTTP server that speaks the Dynatrace Grail `execute query` API
faithfully enough that the **real, unmodified** `make_grail_executor`
(`backend/src/adapters/inbound/dynatrace/grail_executor.py`) can talk to it,
and the real ingest path (`dispatch.py` → `http_normalizer.py` →
`_assembly.py`) assembles correct `SignalObservation`s from its rows.

It exists because the PO's Dynatrace trial expired 2026-07-28 (memory:
`dynatrace-trial-expired`) — no observations arrive, local DynamoDB stays
empty, and nothing data-dependent can be reality-gated. See
`docs/scrum/stories/STORY-148-grail-demo-engine.md` for the full context and
`docs/scrum/sprints/2026-07-28-sprint-62/plan.md` for decision D4.

## What this part covers

- **Row fidelity** (`rows.py`) — `build_row(...)` emits all seven fields the
  real ingest path requires (five from the assembler, two from the HTTP
  normalizer), matching the real captured sample's key/value-type shape.
  `duration_ms`/`response_status_code` are given in natural units and
  converted to the wire's actual nanosecond-string / string-number shape —
  there is no string-typed `duration` parameter to accidentally get wrong.
- **Both DQL grammars** (`query_grammar.py`, `store.py`) — the ingest fetch
  (`build_dql_query`: monitor id + `event.type` + optional watermark bound)
  and the vendor-health existence probe (`build_vendor_health_query`:
  `summarize count()`, `from:now()-2h`), parsed from the real production
  query strings, not guessed at. The watermark bound is PARSED (via the real
  `_assembly.py::parse_ns_timestamp`), never string-compared — a 6-digit
  bound sorts lexicographically before a 9-digit row at the same instant,
  which is the STORY-051 stall reproduced inside this engine if that parsing
  is skipped.
- **The HTTP protocol** (`server.py`) — the ASYNC branch `make_grail_executor`
  speaks: `202` + JSON `{"requestToken": ...}`, then a poll that returns
  `{"state": "SUCCEEDED", "records": [...]}`. Requires the
  `Authorization: Api-Token ...` header. Binds port 0 and reads the actually
  bound port back off the live socket (`DemoEngineServer.base_url`) — see the
  port-safety note below.
- **Proof through the real executor** — `backend/tests/demo_engine/
  test_via_grail_executor.py` drives `make_grail_executor` with its own
  default `httpx.post`/`httpx.get` (no injected fakes) against a running
  `DemoEngineServer`, and asserts assembled `SignalObservation`s. This is the
  specific thing a real HTTP server buys over a fake `Executor` callable
  (decision D4).

## What this part deliberately does NOT cover

No scenario player, no demo fleet config, no end-to-end loop run — that is
**STORY-176** (sprint 63). This story ships only the wire contract: rows,
both query grammars, and the HTTP protocol, proven directly rather than
through a running demo.

## Honest limit: the failure path is tested only with ASSUMED codes

`map_synthetic_status` (`backend/src/adapters/inbound/dynatrace/
health_mapping.py`) maps **only** `code == "0"` / `message == "HEALTHY"` to
`Health.UP` and **raises** `UnknownVendorStatusError` on everything else —
deliberately, because a real failure code has never been observed (the
trial expired before one could be captured), and that module's own
docstring states inventing one would risk silently masking the real value
once verification becomes possible again.

`assumed_failure_codes.py` collects the ONE (unverified, clearly labelled)
non-healthy `(code, message)` pair this engine can build into a row —
`ASSUMED_DOWN_CODE` / `ASSUMED_DOWN_MESSAGE`. Building a row with it proves
only that the **row shape** is still valid; running it through the real,
unmodified `normalize_http_row` still raises `UnknownVendorStatusError`,
exactly as it does for any other unrecognized code
(`backend/tests/demo_engine/test_assumed_failure_codes.py`).

**Wherever this repo says "the failure path is tested," for the demo
engine, that means "tested against an assumed code" — never against
anything Dynatrace has confirmed.** Adding a real failure mapping to
`backend/src/` is a separate, first-class, reviewed decision (STORY-177),
not a side effect of a demo fixture.

## Running the tests

```
pytest backend/tests/demo_engine
```

`tools/demo_engine/` is importable as the top-level package `demo_engine` via
`backend/tests/demo_engine/conftest.py`, which inserts the repo-root
`tools/` directory onto `sys.path` — mirroring the existing `scripts/`
precedent (`backend/tests/conftest.py:16-19`). The directory name uses an
underscore (`demo_engine`, not `demo-engine`) because a hyphenated name is
not importable.

## Port safety (do not reuse the STORY-179 ephemeral-port pattern)

`DemoEngineServer` binds port `0` by default and exposes the port the OS
actually assigned via `base_url`, read directly off the live, still-open
socket (`server_address`) — never a port number computed separately and
handed elsewhere. This is the same defect class STORY-179 found in this
repo's own DynamoDB-Local test fixture (an ephemeral port Docker maps but
Windows doesn't route, so every call to it hangs with no error).
