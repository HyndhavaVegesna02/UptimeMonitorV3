---
title: Zone 3 — the Dynatrace inbound adapter (DQL → canonical observations)
code_refs: [backend/src/adapters/inbound/dynatrace/__init__.py, backend/src/adapters/inbound/dynatrace/_assembly.py, backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py, backend/src/adapters/inbound/dynatrace/dispatch.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, backend/src/adapters/inbound/dynatrace/http_normalizer.py, backend/src/adapters/inbound/dynatrace/query.py, backend/src/adapters/inbound/dynatrace/grail_executor.py, backend/src/core/domain/signal.py, backend/tests/test_dynatrace_adapter.py, backend/tests/test_grail_executor.py, backend/tests/fixtures/dynatrace/clickpath_multi_location.json, backend/tests/fixtures/dynatrace/http_multi_location.json, backend/tests/fixtures/dynatrace/mixed_monitor_types.json, backend/tests/fixtures/dynatrace/unsupported_monitor_type.json, backend/tests/fixtures/dynatrace/grail_http_response.json, backend/tests/fixtures/dynatrace/grail_synthetic_events.json, backend/tests/fixtures/dynatrace/grail_dual_event_types.json, backend/tests/fixtures/dynatrace/grail_response_status_code_variants.json]
verified_sha: 0da9568
verified_sprint: sprint-44
status: verified
---

## Facts (verified against code)

The first inbound adapter (STORY-008, Zone 3, dossier §5/§7/§8). It queries Dynatrace
synthetic monitor results via DQL and normalizes each location execution into a canonical
`SignalObservation` (see [[canonical-types-and-ports]]). Vendor specifics are fully
contained here; `lint-imports` proves the core stays untouched (see [[architecture-boundary]]).

### The pull-cycle entry point
- `fetch_observations(*, signal_key, native_id, watermark, executor, overlap=DEFAULT_OVERLAP)`
  (`adapter.py::fetch_observations`) is what STORY-009's pull loop will call. It builds the DQL query, runs it
  through the injected `executor`, and dispatches every row to its normalizer — returning a
  flat `list[SignalObservation]`, one per location execution, never aggregated (`adapter.py::fetch_observations`).
- `DEFAULT_OVERLAP = timedelta(minutes=5)` (`adapter.py::DEFAULT_OVERLAP`) — the dossier §8 overlap window.

### DQL query builder + the executor seam (`query.py`)
- `build_dql_query(*, native_id, watermark, overlap)` (`query.py::build_dql_query`) is a pure function.
  **It fetches the REAL Grail data object `dt.synthetic.events`** (STORY-016b — reconciled to the live
  tenant; the earlier `dt.synthetic.executions` was an invalid placeholder) and scopes to
  `dt.synthetic.monitor.id == "<native_id>" AND event.type == "http_monitor_execution"`
  (STORY-016c — the canonical per-run verdict row; the `http_step_execution` companion that shares
  the same `event.id` and `timestamp` is excluded at the source so `UNIQUE(observations.source_event_id)`
  can never collide; parameterizing `event.type` per monitor type is out of scope). When `watermark` is
  set it adds a lower bound at `watermark - overlap` on `timestamp` (never the bare watermark, so
  late-landing rows are not missed — dossier §8), emitted as
  `timestamp >= toTimestamp("<ISO Z>")` — **the `toTimestamp()` wrapper is load-bearing**: DQL
  compares a bare string literal against the `timestamp` field without coercion and silently
  matches NOTHING, which stalled ingestion after every first cycle until STORY-051
  (live-confirmed 2026-07-04: bare string → 0 rows, `toTimestamp` → rows to the current minute;
  the covering test also asserts the bare-string form is absent). When `watermark is None`
  (never ingested) it adds no time bound and the first pull reads whatever Grail's DEFAULT scan
  timeframe covers (~2h observed live — NOT "everything"; an explicit query timeframe is a
  STORY-051-noted follow-up); `| sort timestamp asc`.
- `watermark` must be tz-aware UTC — a naive datetime is rejected (`query.py::build_dql_query`), mirroring
  the core's own `observed_at` validator (`core/domain/signal.py::SignalObservation._require_utc`).
- `native_id` is interpolated unescaped into the query string (`query.py::build_dql_query`); a comment
  documents the trusted-input assumption (vendor config id, read-only Grail fetch — no injection
  vector). It is still validated first: any `native_id` containing a DQL-breaking character
  (`"`, backslash, or a newline — `query.py::_DQL_BREAKING_CHARS`) raises the named
  `InvalidNativeIdError` (`query.py::InvalidNativeIdError`) rather than silently malforming the query — rejected,
  not escaped/sanitized (STORY-021).
- `Executor = Callable[[str], list[dict]]` (`query.py::Executor`) is the injected live-DQL seam.
  Production (composition root) injects a real HTTP-backed one; **every test injects a fake** —
  no live Dynatrace call is ever made in a test (working agreement: pure core, mockable edges).

### Real Grail DQL executor (`grail_executor.py`, STORY-016 → reconciled STORY-016b)
- `make_grail_executor(*, env_url, api_token, http_post=httpx.post, http_get=httpx.get,
  poll_attempts=60, poll_interval_seconds=1.0, sleep_func=time.sleep) -> Executor`
  (`grail_executor.py::make_grail_executor`) returns the real `Executor` closure.
- **The Grail query API is ASYNCHRONOUS** (STORY-016b, proven by a live probe): POST the DQL to
  `{env_url}/platform/storage/query/v1/query:execute` (`Authorization: Api-Token <token>`, body
  `{"query": <dql>}`). It returns HTTP **202** `{"state":"RUNNING","requestToken":"…"}`; the executor
  then polls `…/query:poll?request-token=…` (`http_get`) until a terminal state — `SUCCEEDED` →
  return `result.records` (`[]` if absent); `FAILED`/`CANCELLED`/unknown state → raise `GrailQueryError`;
  poll budget `poll_attempts × poll_interval_seconds` (default 60s) exhausted → raise. A synchronous
  200-with-records response is still handled (`_extract_records` reads `result.records` or `records`).
  Non-2xx on execute or poll, an unparseable body, or a 202 without a token all raise the named
  `GrailQueryError` (`grail_executor.py::GrailQueryError`, a `RuntimeError`).
- The `http_post`/`http_get`/`sleep_func` seams keep it unit-testable with NO live call and NO real
  waiting; it never leaks `httpx.Response` across the boundary (returns `list[dict]`). Wired by
  `composition/run.py::build_live_loop` (see [[ingest-service-and-pull-loop]]). Tested in
  `backend/tests/test_grail_executor.py` driving execute→202→poll→SUCCEEDED, FAILED-state,
  poll-exhaustion, sync-fallback, and empty-records, all against fakes.

### Normalizer dispatch (`dispatch.py`) — the additive seam
- `_NORMALIZERS` (`dispatch.py::_NORMALIZERS`) maps a vendor **`event.type`** string (STORY-016b — the
  real Grail dispatch key; the earlier `synthetic_test.type` does not exist in live data) to a
  normalizer: `"http_monitor_execution" -> normalize_http_row` (STORY-016c — changed from the
  previous `http_step_execution` which was the wrong canonical row). Each HTTP monitor execution emits
  TWO event types sharing the same `event.id` and `timestamp`: `http_monitor_execution` (the canonical
  per-run overall verdict — the one we ingest) and `http_step_execution` (the per-step companion — the
  one we exclude at the source via the query filter in `build_dql_query`). The step row is intentionally
  absent from the registry to state intent clearly; if it somehow reached dispatch (past the query
  filter) it would raise `UnsupportedMonitorTypeError` — fail-loud, defense-in-depth (AC3, STORY-016c).
  Clickpath's real `event.type` is unknown / out of scope; do not guess it. Adding a future type is
  one registry entry + one normalizer module — no existing call site changes.
- `normalize_row` raises `UnsupportedMonitorTypeError` (`dispatch.py::UnsupportedMonitorTypeError` and `dispatch.py::normalize_row`) for any unmapped
  `event.type` rather than mis-normalizing. `normalize_rows` (`dispatch.py::normalize_rows`) maps it over a sequence,
  one observation per row, in input order, mixed monitor types/locations normalized independently.

### Per-type normalizers + shared assembly
- `normalize_http_row` (`http_normalizer.py::normalize_http_row`, `NATIVE_KIND="http"`) and
  `normalize_clickpath_row` (`clickpath_normalizer.py::normalize_clickpath_row`, `NATIVE_KIND="clickpath"`,
  optional `raw_ref`) each compute their own `Health` then delegate to the shared assembler.
- The clickpath normalizer reads ONLY the monitor-level `execution.outcome` that Dynatrace
  already collapsed the per-step journey into; it ignores the `steps` array entirely — step
  detail is never modelled on the canonical shape (`clickpath_normalizer.py` ("Browser-clickpath synthetic monitor normalizer"), AC3).
- `assemble_observation(row, *, signal_key, health, native_kind, raw_ref=None)` (`_assembly.py::assemble_observation`)
  is the single home of the timestamp parse + the `SignalObservation`/`Provenance` construction. The
  vendor monitor type lives only in `Provenance.native_kind`; `system="dynatrace"`,
  `native_id=row["dt.synthetic.monitor.id"]`.
- **Real Grail row field shape (STORY-016b, fixture `grail_synthetic_events.json`):** `timestamp`
  (9-digit **nanosecond** ISO → `observed_at`), `event.id` (→ `source_event_id`),
  `dt.synthetic.monitor.id` (→ `native_id`), `event.type` (dispatch key), `dt.entity.synthetic_location`
  (a location ENTITY id → `location`; display-name resolution is out of scope, needs
  `storage:entities:read`), `result.status.code`/`result.status.message` (→ health), and
  `result.statistics.duration` (**nanoseconds** → optional `latency_ms`, `int(ns)//1_000_000`).
  STORY-064: `result.statistics.response_status_code` (a STRING-typed number on the real wire,
  e.g. `"200"` — confirmed by the 2026-07-12 live probe, monitor
  `HTTP_CHECK-38B092E93932C002`) -> optional int `response_status_code`
  (`_assembly.py::assemble_observation`); missing or unparsable -> `None`, never a crash — same
  optional-parse style as `latency_ms`. Previously this field was read nowhere and silently
  dropped.
- **Nanosecond-timestamp parse:** `parse_ns_timestamp` (`_assembly.py::parse_ns_timestamp`) truncates
  fractional seconds to 6 digits (µs) before `datetime.fromisoformat`, because Grail emits 9-digit ns
  precision (`…742000000Z`) which `fromisoformat` would otherwise reject. Handles a `Z` or explicit
  `+00:00` suffix and a no-fractional timestamp.
- A missing REQUIRED field (`timestamp`, `event.id`, `dt.synthetic.monitor.id`, `event.type`,
  `dt.entity.synthetic_location`) surfaces as a named `MalformedDqlRowError`
  (`_assembly.py::MalformedDqlRowError`), not a bare `KeyError` (STORY-020), via the shared
  `require_field` helper (`_assembly.py::require_field`). `result.statistics.duration` stays optional
  (read via `.get`) — its absence is NOT malformed.

### Health mapping (`health_mapping.py`) — the only place vendor status words are read
- **Live HTTP path (STORY-016b):** `map_synthetic_status(*, code, message)`
  (`health_mapping.py::map_synthetic_status`) maps the real `result.status` fields: `code == "0"` (or
  `message == "HEALTHY"`) → `Health.UP`. Any other value raises the named `UnknownVendorStatusError`
  (`health_mapping.py::UnknownVendorStatusError`) — it is **fail-loud, NOT guessed**: only the healthy
  value is known today; the real DOWN/DEGRADED code(s) are captured during the live verification
  (STORY-016b plan T6/AC6) and the mapping is extended THEN. Inventing failure codes was explicitly
  rejected at review (it would silently mask the real failure value the live run is meant to observe).
- **Legacy clickpath path:** `map_execution_outcome(outcome)` (`health_mapping.py::map_execution_outcome`,
  `success→UP`/`failure→DOWN`/`partial→DEGRADED`, raises `UnknownVendorOutcomeError`) is still used by
  `clickpath_normalizer` against the old `execution.outcome` field. Browser clickpath is out of the
  live HTTP scope (not in the live dispatch registry), so this path is retained but not exercised live.

### Tests + fixtures
- `backend/tests/test_dynatrace_adapter.py` (33 tests) runs entirely off committed JSON fixtures
  under `backend/tests/fixtures/dynatrace/` (`http_multi_location.json`,
  `clickpath_multi_location.json`, `mixed_monitor_types.json`, `unsupported_monitor_type.json`,
  `grail_synthetic_events.json`, `grail_dual_event_types.json`,
  `grail_response_status_code_variants.json` — STORY-064).
- `grail_synthetic_events.json` (STORY-016c): reconciled to the real live probe
  (2026-06-29) — two distinct `http_monitor_execution` records (event.id 156345503298/156345503299,
  ns timestamp, ns duration, `result.state` present). STORY-064: its (and
  `grail_dual_event_types.json`'s) `response_status_code` values were corrected from a JSON int
  `200` to the real STRING shape `"200"` (a 2026-07-12 plan-verifier finding — an int-typed fixture
  row never drives the normalizer's str->int parse, so it would have shipped green-but-untested).
- `grail_dual_event_types.json` (STORY-016c): AC5 sibling fixture — one execution represented as
  BOTH its `http_monitor_execution` row AND its same-`event.id` `http_step_execution` companion.
  Used by the dedup demonstration test to prove exactly one observation results when the canonical
  row is fed to dispatch and the companion would raise if it reached dispatch.
- `grail_response_status_code_variants.json` (STORY-064): two records derived from the 2026-07-12
  live probe sample (`docs/scrum/sprints/2026-07-12-sprint-44/probe-sample-http-monitor-execution.json`,
  monitor `HTTP_CHECK-38B092E93932C002`) covering `response_status_code`'s two edge cases: the
  field entirely absent, and a non-numeric string (`"N/A"`) — both must normalize to `None`, never
  raise.

## Inference (synthesis, not verified)
- The HTTP path's data object (`dt.synthetic.events`), field names, async query shape, ns timestamps,
  and the canonical `event.type` (`http_monitor_execution`) are now RECONCILED to the PO's live tenant
  (STORY-016b probe + STORY-016c reconciliation, 2026-06-29). The one value still unverified is the
  real failure `result.status.code`/`message` for a DOWN/DEGRADED execution — captured in the AC6
  live verification (the loop fails loud until then). The clickpath path remains on the old
  illustrative `execution.outcome` shape (out of live scope).

## History
- sprint-4: created (STORY-008). Documents the Dynatrace inbound adapter as built + the STORY-008
  fix-loop-1 shared-assembly extraction. Verified at 834b90c (re-stamped to 40ed985 at merge).
- sprint-5: STORY-020 — required DQL fields now raise the named `MalformedDqlRowError` via a shared
  `require_field` helper (replacing bare `KeyError`). Re-verified at d3a864d.
- sprint-6: STORY-021 — `build_dql_query` now rejects a `native_id` containing a DQL-breaking
  character (`"`, backslash, newline) via the named `InvalidNativeIdError`, instead of silently
  interpolating it unescaped. Re-verified at ae5f880.
- sprint-20: STORY-016 — added the real `grail_executor.py` (`make_grail_executor` + `GrailQueryError`)
  behind the `query.py::Executor` seam: the HTTP-backed DQL executor the live loop injects. The
  field-name reconciliation note below still stands (confirm against the live tenant). Re-verified at d9c2a77.
- sprint-21: STORY-016b — RECONCILED the HTTP path to the live tenant (probe 2026-06-29): query targets
  `dt.synthetic.events` filtered on `dt.synthetic.monitor.id`; the executor handles the ASYNC query
  (202 → poll `query:poll` until SUCCEEDED) with a real poll budget; dispatch keys on `event.type`
  (`http_step_execution` at the time — wrong, fixed in STORY-016c); the assembler maps the real fields
  incl. ns-timestamp truncation + ns→ms latency; health via the fail-loud `map_synthetic_status`
  (HEALTHY/0→UP, no invented failure codes). Re-verified at 213034b.
- sprint-22: STORY-016c — Fixed the dispatch registry key from `http_step_execution` to
  `http_monitor_execution` (the canonical per-run verdict row); added `event.type ==
  "http_monitor_execution"` filter to `build_dql_query` to exclude the same-`event.id`
  `http_step_execution` companion at source; reconciled `grail_synthetic_events.json` to real probe
  values; added `grail_dual_event_types.json` for AC5 dedup demonstration; ruff exclude for `.agents/`
  (pre-existing DoD gate fix). The AC6 live verification PASSED (loop ran against the live tenant: 119
  real observations ingested, health UP, two locations, ns→ms latency, `distinct source_event_id ==
  total` so no `UNIQUE(source_event_id)` collision — the dedup works end to end). The real failure
  `result.status` code remains TBD (no failing run could be induced this sprint; `map_synthetic_status`
  stays fail-loud). Re-verified at ed19084.
- sprint-44 (STORY-064, pilot): `assemble_observation` now also extracts
  `result.statistics.response_status_code` (STRING-typed on the real wire) -> optional int
  `response_status_code` (Facts updated above); previously read nowhere and dropped. The two
  committed `grail_synthetic_events.json`/`grail_dual_event_types.json` fixtures' `200` values were
  corrected from JSON int to the real string shape; added `grail_response_status_code_variants.json`
  (absent/non-numeric edge cases, derived from the 2026-07-12 live probe sample). Test count 31 ->
  33. Caught by manual re-verification, not the mechanical sweep: this article's (and
  [[canonical-types-and-ports]]'s) frontmatter carried a trailing inline comment on the `status:`
  line that `yt_wiki.py`'s frontmatter parser reads as part of the value, so the sweep silently
  skipped both articles rather than reporting them stale — normalized the `status:` line to the
  plain form and flagged the parser gap as a candidate backlog item. See
  [[canonical-types-and-ports]] for the paired `SignalObservation` domain field,
  [[persistence-adapters]]/[[migrations-and-db]] for persistence/migration, and
  [[api-five-file-convention]] for the DTO/service side. verified_sha -> 0da9568.
