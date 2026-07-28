---
id: STORY-148
title: Grail-shaped demo engine, part 1 — the wire contract (rows, both query grammars, HTTP protocol)
type: chore
---

## Context

The PO's Dynatrace trial expired 2026-07-28. No observations arrive, so local DynamoDB stays
empty, nothing data-dependent can be reality-gated, and the multi-monitor / multi-location
correctness work agreed this sprint-line (breadth ceiling, per-component rollup, freshness)
cannot be exercised against realistic scenarios **at any price**.

The existing `sample_mode` feature does not help: `SampleModeIngest` decorates
`SignalIngestPort` and flips **already-normalized** observations to `DOWN`
(`backend/src/composition/sample_mode.py:66-72`), so it needs real data to have anything to
flip.

The seam for a substitute already exists and is documented for exactly this purpose:

```python
# backend/src/adapters/inbound/dynatrace/query.py:32
Executor = Callable[[str], list[dict]]
#: Production wiring (composition root) will inject a real HTTP-backed
#: implementation; every test in this package injects a fake instead.
```

PO approved option (b) — a local HTTP server speaking the Grail `execute query` API — over a
fake `Executor` callable, because it needs **zero production-code changes** (one env var) *and*
is more faithful, additionally exercising `make_grail_executor`, the real HTTP client, auth
headers and response parsing. Decision recorded as D4 in
`docs/scrum/sprints/2026-07-28-sprint-62/decisions-and-future-work.md`.

**This story is part 1 of 2.** It builds the engine's *wire contract* and nothing else: rows
that are indistinguishable from real Grail rows, both DQL grammars the production code actually
emits, and the HTTP protocol `make_grail_executor` actually speaks — proven through the **real**
executor. STORY-176 then adds the scenario player, the demo fleet config, and the end-to-end
loop run. The split is deliberate: fidelity is the whole value of the approach, three separate
code paths return **silently empty** when it is wrong, and a "the loop ran" demo built on a
subtly-wrong wire would look like success while proving nothing.

It lives in `tools/demo_engine/` at the repo root, **outside `backend/src/`**, so it can never
enter the production image and import-linter contracts are untouched.

## Acceptance Criteria

- [ ] **AC1 (required fields — all SEVEN)** — The demo row carries every field the ingest path
      requires, verified field-by-field against the real captured sample
      `backend/tests/fixtures/dynatrace/grail_synthetic_events.json`. Five are required by the
      assembler (`_assembly.py:86,108,111,114`): `timestamp`, `event.id`,
      `dt.synthetic.monitor.id`, `dt.entity.synthetic_location`, plus `event.type` for dispatch.
      **Two more are required by the normalizer** and were missing from the original draft:
      `result.status.code` and `result.status.message`, both read via `require_field`
      (`http_normalizer.py:22-23`) and both feeding `map_synthetic_status`. A row built to the
      five-field list passes a naive fidelity test and then raises `MalformedDqlRowError` on the
      first row through the loop — so the test asserts all seven, by key **and value type**,
      against the fixture.
- [ ] **AC2 (optional fields, with their real scale)** — `result.statistics.duration` and
      `result.statistics.response_status_code` are emitted with the real wire's type *and scale*:
      both are **strings**, and `duration` is a count of **NANOSECONDS** (fixture:15 —
      `"755000000"`, which `_assembly.py:92` divides by 1_000_000 to get 755 ms). A test asserts
      a scale-sane round trip — emit a row intended as 755 ms, assert the assembled
      `SignalObservation.latency_ms == 755`. Type-equality alone is insufficient here: emitting
      `"755"` (milliseconds) is the same type and yields `latency_ms == 0` for every observation
      in the fleet.
- [ ] **AC3 (ingest query grammar)** — The engine parses the query `build_dql_query` emits and
      honours **all three** clauses (`query.py:85-97`), not two: the
      `dt.synthetic.monitor.id == "<native_id>"` scope filter, the
      `event.type == "http_monitor_execution"` filter, and the
      `timestamp >= toTimestamp("<iso>")` lower bound when a watermark exists. Rows are returned
      in `timestamp asc` order. Tests prove a query for monitor A never returns monitor B's rows,
      that a non-matching `event.type` returns nothing, and that the watermark bound excludes
      older rows.
- [ ] **AC4 (the watermark bound must be parsed, not string-compared)** — `query.py:96` emits
      `since.isoformat().replace("+00:00","Z")` → a **6**-digit fraction
      (`…40.746000Z`), while rows carry **9** (`…40.746000000Z`, fixture:4). A lexicographic
      comparison puts `'0' < 'Z'`, so a row at the *same instant* sorts before the bound and is
      wrongly excluded — the demo would ingest one cycle and then stall, reproducing the exact
      STORY-051 failure mode inside the demo engine. Both sides are parsed to datetimes before
      comparison, and a test covers the precision boundary specifically (row `…746000000Z`
      against bound `…746000Z` must be **included**).
- [ ] **AC5 (the SECOND query grammar — runs at every startup, for every signal)** — The engine
      also answers `build_vendor_health_query` (`composition/vendor_health.py:40-53`), a
      different grammar entirely: `fetch dt.synthetic.events, from:now()-2h | filter
      dt.synthetic.monitor.id == "…" | summarize count()`, whose response must be a single row
      keyed literally `"count()"` (`_extract_count`, `vendor_health.py:56-76`).
      `check_vendor_id_health` runs before any loop is built (`run.py:192-196`) for **every**
      configured signal, so an engine that answers only the ingest grammar returns `[]` for all
      of them and the startup log fills with prominent warnings claiming every monitor id is
      dead — polluting the very evidence STORY-176's reality gate collects, and mimicking the
      STORY-070 drift defect. A test asserts a live count for a known monitor and 0 for an
      unknown one.
- [ ] **AC6 (the HTTP protocol, pinned literally)** — The server implements what
      `make_grail_executor` actually calls (`grail_executor.py:43-97`): POST
      `{env_url}/platform/storage/query/v1/query:execute` with body `{"query": …}` and header
      `Authorization: Api-Token …`. It responds in the **asynchronous** mode the real vendor
      uses — `202` + `requestToken`, then `GET …/query:poll?request-token=…` returning
      `state: "SUCCEEDED"` with `{"records": [...]}`. Async is chosen deliberately: a sync-only
      server exercises only the executor's *fallback* branch, which would undercut D4's stated
      reason for preferring option (b) over a fake callable. Note the failure mode being guarded
      against — at `grail_executor.py:97`, a non-202 response with no `requestToken` returns
      `[]` **silently**.
- [ ] **AC7 (proven through the real executor, not a fake)** — At least one test drives
      `make_grail_executor(env_url=<local server>, api_token=<any>)` against the running demo
      server and asserts assembled `SignalObservation`s come back correct. This is the specific
      thing option (b) buys over option (a), so it is asserted rather than assumed.
- [ ] **AC8 (assumptions labelled, not buried)** — `map_synthetic_status` maps only
      `"0"`/`"HEALTHY"` and raises on everything else (`health_mapping.py:65-70`), because a real
      failure code has never been observed. Any failure code the demo engine emits is therefore
      an **assumption**. All such codes live in ONE named constant with a comment marking them
      unverified pending trial renewal, and the demo README states plainly that "the failure
      path is tested" means "with assumed codes".
- [ ] **AC9 (production untouched, and the tests actually run)** — `git diff` for this story
      touches only `tools/`, `docs/`, `CLAUDE.md`, and test files under `backend/tests/`. **No
      file under `backend/src/` is modified**, verified mechanically from the commit range.
      Tests live under `backend/tests/` because `pyproject.toml:29` sets
      `testpaths = ["backend/tests"]` — tests placed under `tools/` would never run while the
      DoD gate stayed green. The engine imports via the existing repo-root `sys.path` precedent
      (`backend/tests/conftest.py:16-19`); the directory is `tools/demo_engine/` with an
      underscore, since `demo-engine` is not an importable package name. Engine code is subject
      to `ruff check` and `ruff format` — `tools/` is **not** in ruff's exclude list
      (`pyproject.toml:111`).
- [ ] **AC10** — All five backend DoD gate commands exit 0.

## Open Questions

None.

## History

- 2026-07-28: drafted. PO chose option (b) (local Grail-shaped HTTP server + scenario files)
  over option (a) (fake `Executor`) and option (c) (also driving CI fixtures — deferred, may
  grow out of this). Recorded as D4. Removal of the superseded `sample_mode` feature is
  deliberately NOT folded in — it has its own removal inventory
  (`docs/scrum/wiki/sample-mode.md`) spanning port/adapter/fake/API, and belongs in its own
  story.
- 2026-07-28: **split and amended after `yt-plan-verifier` (pre-lock, verdict GAPS).** The
  original single 5-pt story was assessed at 7–8 pts of real work and is now two stories: this
  one (the wire contract) and STORY-176 (scenario player, demo fleet, end-to-end gate). Seven
  substantive corrections, each traced to verified code: (1) the required-field set was 5, not 7
  — `result.status.code`/`result.status.message` are `require_field` in the *normalizer*, which
  the original list missed because it was sourced from `_assembly`'s docstring; (2) `duration` is
  a nanosecond count carried as a string, a units/scale trap that type-equality alone cannot
  catch; (3) the ingest grammar has three clauses, not the "both clauses" the draft claimed;
  (4) the watermark bound cannot be string-compared (6-digit bound vs 9-digit rows); (5) a
  **second** query grammar (`vendor_health.py`) runs at every startup for every signal and was
  entirely unaccounted for; (6) the HTTP envelope, endpoints, auth header and async protocol
  were never specified, and getting them wrong returns `[]` silently; (7) `tools/demo-engine/`
  is not importable and tests placed there would never run under `testpaths`.
</content>
