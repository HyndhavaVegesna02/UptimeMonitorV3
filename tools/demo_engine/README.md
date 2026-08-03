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
  and the vendor-health existence probe (`build_vendor_health_dql`:
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

No scenario player, no demo fleet config, no end-to-end loop run — that was
**STORY-176** (sprint 63). This story ships only the wire contract: rows,
both query grammars, and the HTTP protocol, proven directly rather than
through a running demo.

## Part 2a (STORY-176, sprint 63): the scenario player, the demo fleet, and the publish guard

**Still no end-to-end loop run — that is STORY-182 (sprint 64).** This part
ships everything that must be true BEFORE a loop may safely be started:

- **The scenario player** (`scenario.py`) — a scenario YAML declares, per
  signal, an ordered list of CYCLES; each cycle names which locations report
  `UP` that cycle (a location's absence from the list is the only other
  outcome this engine can express — see "Scope honesty" above).
  `expand_scenario` is **past-anchored**: the scenario's LAST cycle lands at
  `end_time` (typically `clock.now()`), and earlier cycles land successively
  further back at the monitor's own `interval_seconds`. This is deliberate,
  not incidental — a forward player (t0 -> now) would have every cycle beyond
  `end_time + 5min` silently quarantined by `ingest_service.py`'s
  `FUTURE_TOLERANCE`, and the whole declared ladder would only become visible
  once wall-clock time caught up to it. Past-anchoring means the whole ladder
  is inside `orchestrate.py`'s rolling 7-cycle window on the very first
  query.
- **The demo fleet** (`config/demo/`, repo root — **never** `config/apps/`) —
  a fictional fleet in STORY-146's nested config shape: 13 components, 41
  signals, 4 declared locations, freshness blocks, every monitor at
  `interval_seconds <= 60`. `config/demo/scenarios/` covers every case
  reachable without a failure-code mapping: a clean fleet, a fully dark
  location, a fully dark monitor, staggered intervals, and a
  late-returning monitor.
- **The publish guard — config-only, and it needs `CONFIG_DIR` set on BOTH
  processes that could build a live publisher, not just the loop.**
  `config/demo/` declares **no** `statuspage_component_id` on any component,
  so `Config.statuspage_mapping()` is `{}` and `build_publisher`
  (`backend/src/composition/publish_helper.py:211`) falls through to a
  `LoggingPublisher` delegate **even with real Statuspage credentials
  present** in the repo-root `.env` (`composition/run.py:178`'s
  `load_dotenv()` walks up from the source file, not CWD, so it supplies
  those credentials regardless of the launch directory). TWO composition
  roots build a live publisher from them, and both read `CONFIG_DIR`:
  - the loop (`composition/run.py::main` -> `build_live_loop`);
  - the API's **approve trigger** (`composition/app.py::create_app` — no
    `config_dir` argument in the documented local-run recipe, so `CONFIG_DIR`
    alone governs which config it seeds and maps).

  Setting `CONFIG_DIR=config/demo` on only ONE of the two still leaves the
  other resolving the default `config/apps` (`settings.py:32`), which
  declares a real `statuspage_component_id`
  (`config/apps/httpcheck.yaml:8`) — so both processes must point at the
  demo directory together, or the guard does not hold end-to-end. Demo
  component ids are additionally kept **disjoint** from `config/apps`'s:
  `StatuspagePublisher` keys on the canonical component id
  (`adapters/outbound/statuspage/__init__.py:41-46`), so a colliding id would
  PATCH the real page even with `CONFIG_DIR` set correctly everywhere else.

  All four checks are asserted **in-process** (`backend/tests/
  test_demo_fleet_config.py`) — no v1 route exposes the runtime
  mapping/publisher/config, so this cannot be asserted over HTTP without a
  `backend/src/` change this story does not make.

**No demo loop is started by this story.** `decide` publishes recoveries with
no human gate (`core/services/decide.py:122-126` decides, `:171-172`
publishes) — the run, and its own two-sided gate, are STORY-182.

## Part 2b (STORY-182, sprint 64): the loop HAS now been run, and its three-sided gate

The harness lives alongside this engine, in the sibling `tools/demo_loop_gate/`
package (not inside `demo_engine/` itself, since it composes the engine, the
config layer, and two real subprocesses rather than extending the wire
contract):

- **The fleet-wide coverage artifact** (`tools/demo_loop_gate/
  fleet_coverage.py`) — `config/demo/scenarios/*.yaml` (this file's own
  "Part 2a" section, above) covers only 6 of the fleet's 41 signals by
  design; an unseeded monitor id returns `[]` (`store.py`'s ingest-query
  filter), which both starves `/history` and makes
  `check_vendor_id_health` warn. `build_fleet_row_store` builds one
  `SignalScenario` **in code** from the loaded `Config` — monitor
  id/interval from the signal, cycle locations from that signal's own app's
  declared `locations:` block — and expands it with the real
  `expand_scenario`: 820 rows (41 signals x 5 cycles x 4 locations), all at
  or before `end_time`, all inside the vendor-health probe's trailing 2h
  window. The builder route (over a second checked-in YAML) was chosen so
  the 4 locations and each signal's own interval are derived from config,
  never duplicated — and constructing `SignalScenario` in code is exactly
  the path STORY-184's `interval_seconds` type/sign invariant guards, which
  is why that story had to land first.
- **The positive-side harness** (`tools/demo_loop_gate/harness.py::
  run_positive_side`) — re-runnable via `python tools/demo_loop_gate/
  harness.py`. Creates fresh throwaway observations+control tables, starts
  an embedded local demo engine seeded with the coverage artifact above,
  launches the API as a real `uvicorn` subprocess and the loop as the real,
  unmodified `python -m src.composition.run` subprocess — both with
  `CONFIG_DIR=config/demo` and the same fresh table names (never a human
  setting the pair on only one terminal) — asserts every AC1 precondition,
  waits adaptively (polling, never a blind fixed sleep) for the last signal
  in build order to finish ingesting, terminates the loop (exception-safely:
  `_terminate_loop_after` reaps it in a `finally` even if the wait itself
  raises) before asserting AC3 ingest / AC4 vendor-health / AC5 empty
  approvals, then tears both processes down with a genuine OS-level PORT
  check (`_port_is_free`, a real `connect_ex`) plus the process's own
  reaped returncode — **not** "OS-level PID verification": `Popen.poll()`
  read immediately after `Popen.wait()` returns only re-reads the already-
  cached returncode, it never asks the OS again, so it is recorded as
  `reaped_returncode_observed`, not treated as independent proof.
- **The two discrimination sides, independently callable** —
  `tools/demo_loop_gate/guard_reality_gate.py` (no pytest, no DynamoDB, no
  network: builds the real `build_publisher` chain twice and asserts the
  full `_delegate` chain of type names differs between a `{}` mapping and a
  throwaway non-empty one) and `tools/demo_loop_gate/
  backfill_reality_gate.py` (drives the real `check_vendor_id_health`
  against an empty `DemoRowStore` vs. the coverage store above and asserts
  the drift/healthy-INFO counts differ).

Verified green: AC1(a)-(e) all recorded (including STORY-176's
publish-guard regression re-run); AC2 fresh tables; AC3 all 41 signals
ingest 20 rows / 4 distinct locations each; AC4 zero drift warnings, 41
`Vendor-id health OK` INFO lines; AC5 `/approvals` == `[]`. Full detail:
`docs/scrum/stories/STORY-182-demo-loop-run-and-gate.md`.

## Honest limit: failure codes are provisional and unverified

`map_synthetic_status` (`backend/src/adapters/inbound/dynatrace/health_mapping.py`)
maps healthy rows to `Health.UP` and maps `("1", "UNHEALTHY")` -> `Health.DOWN` and
`("2", "DEGRADED")` -> `Health.DEGRADED` via `PROVISIONAL_STATUS_MAPPING` (STORY-177).

`assumed_failure_codes.py` imports these provisional codes directly from
`health_mapping.py`.

**Wherever this repo says "the failure path is tested," for the demo
engine, that means "tested against provisional assumed codes" — unverified
pending live Dynatrace trial renewal (STORY-154).**


## Running the tests

```
pytest backend/tests/demo_engine
```

`tools/demo_engine/` is importable as the top-level package `demo_engine` via
the SHARED `backend/tests/conftest.py`, which inserts the repo-root `tools/`
directory onto `sys.path` (`backend/tests/conftest.py:28-30`) alongside the
existing `scripts/` precedent (`backend/tests/conftest.py:24-26`) — NOT a
separate `backend/tests/demo_engine/conftest.py` (deleted): pytest resolves a
bare, `__init__.py`-less `conftest.py`'s module name from its basename alone,
so two such files both named `conftest.py` collide on the same
`sys.modules['conftest']` entry (`backend/tests/conftest.py:9-14`; it broke
`test_dynamo_local.py`'s `from conftest import provide_dynamo_local`). The
directory name uses an underscore (`demo_engine`, not `demo-engine`) because a
hyphenated name is not importable.

## Port safety (do not reuse the STORY-179 ephemeral-port pattern)

`DemoEngineServer` binds port `0` by default and exposes the port the OS
actually assigned via `base_url`, read directly off the live, still-open
socket (`server_address`) — never a port number computed separately and
handed elsewhere. This is the same defect class STORY-179 found in this
repo's own DynamoDB-Local test fixture (an ephemeral port Docker maps but
Windows doesn't route, so every call to it hangs with no error).
