---
title: Zone 3 — the Dynatrace inbound adapter (DQL → canonical observations)
code_refs: [backend/src/adapters/inbound/dynatrace/__init__.py, backend/src/adapters/inbound/dynatrace/_assembly.py, backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py, backend/src/adapters/inbound/dynatrace/dispatch.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, backend/src/adapters/inbound/dynatrace/http_normalizer.py, backend/src/adapters/inbound/dynatrace/query.py, backend/src/adapters/inbound/dynatrace/grail_executor.py, backend/src/core/domain/signal.py, backend/tests/test_dynatrace_adapter.py, backend/tests/test_grail_executor.py, backend/tests/fixtures/dynatrace/clickpath_multi_location.json, backend/tests/fixtures/dynatrace/http_multi_location.json, backend/tests/fixtures/dynatrace/mixed_monitor_types.json, backend/tests/fixtures/dynatrace/unsupported_monitor_type.json, backend/tests/fixtures/dynatrace/grail_http_response.json, backend/tests/fixtures/dynatrace/grail_synthetic_events.json, backend/tests/fixtures/dynatrace/grail_dual_event_types.json, backend/tests/fixtures/dynatrace/grail_response_status_code_variants.json]
tier: map
verified_sprint: sprint-68
status: verified
# Re-verified 2026-07-30 (sprint-65, STORY-177/190 fix round). Facts REWRITTEN, not re-stamped:
# map_synthetic_status is now a THREE-step resolution (healthy OR-rule -> exact provisional tuple
# -> raise), and dispatch gained a lenient counterpart returning NormalizationOutcome. The old
# fail-loud-only description and its 'live verification will supply the real codes' reasoning are
# kept as an explicit SUPERSEDED note, because the trial expired and that verification cannot happen.
# Re-verified 2026-07-30 (sprint-65 quality-review round). NEW Fact: normalize_rows_lenient now
# catches ValueError, not three named classes -- a PRESENT-but-invalid field (unparsable timestamp,
# null location) previously escaped and still stalled the signal.
# tier: map, `verified_sha` dropped 2026-08-12 (yourteam 2.3.0): the staleness baseline is now
# this article's own last commit, derived by git, so there is no stamp to keep current.
# WHAT THIS EDIT DID AND DID NOT VERIFY: it did not re-read these Facts against code. It
# established, per-article, that NO code_ref has moved since this article's last commit
# (`git diff <that commit>..HEAD -- <code_refs>` -> empty, and the sweep is CLEAN at HEAD),
# so the verification earned at sprint 68 is not invalidated by anything since. That is
# the same guarantee `status: verified` has always carried here; the frontmatter migration
# adds no new claim. Articles nobody could make that statement for were demoted to `stale`
# in the same pass, not laundered.
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
  the same `event.id` and `timestamp` is excluded at the source so the two rows never collide on the
  same idempotency key (the `EVT#<event_id>`/`DEDUPE` marker item,
  `dynamo_observation_repository.py:58-62` — corrected STORY-181, sprint-63; the comment had cited a
  SQL `UNIQUE` constraint that never existed here); parameterizing `event.type` per monitor type is
  out of scope). When `watermark` is
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
  (`"`, backslash, `\n`, or `\r` — the FOUR members of `query.py::_DQL_BREAKING_CHARS`) raises the
  named `InvalidNativeIdError` (`query.py::InvalidNativeIdError`) rather than silently malforming
  the query — rejected, not escaped/sanitized (STORY-021). `\r` is one of the four guarded
  characters because the constant defends the DQL string literal against ANY breaking character
  regardless of provenance — the guard does not depend on a specific ingress story. The one
  VERIFIED route to a real `\r` in this scalar is an explicit `\r` escape inside a
  double-quoted YAML scalar (e.g. `native_id: "MON\rA"`). **Ruled out, with the reason:** a
  CRLF-contaminated `config/apps/*.yaml` on this Windows-developed repo does NOT reach this
  check — `load_config` reads via `yaml_path.read_text(encoding="utf-8")`
  (`composition/config.py::load_config`), and `Path.read_text()` applies universal-newline
  translation, turning `\r\n` into `\n` before PyYAML ever sees it (disproved end-to-end,
  twice — on a scratch copy with every line ending rewritten to CRLF, `native_id` still loaded
  with `contains_CR=False`). In the loop process, `composition/run.py::main` always runs the
  vendor-health probe — sharing the same `_reject_dql_breaking_native_id` validation — BEFORE
  `seed_topology_dynamo`/`build_live_loop` (`run.py::main`, the probe call precedes both), so a
  misconfigured `native_id` there always aborts the loop process at startup; the per-cycle
  degraded-ingest outcome (`run_periodic`, [[ingest-service-and-pull-loop]]) is not reachable for
  this particular error in that process.
- `Executor = Callable[[str], list[dict]]` (`query.py::Executor`) is the injected live-DQL seam.
  Production (composition root) injects a real HTTP-backed one; **every test injects a fake** —
  no live Dynatrace call is ever made in a test (working agreement: pure core, mockable edges).
- **`build_vendor_health_dql(*, native_id)` (`query.py::build_vendor_health_dql`, relocated here
  from `composition/vendor_health.py` at STORY-204, ZR-8 finding 2) is the OTHER DQL shape this
  module builds** — a cheap, bounded-window (`query.py::HEALTH_CHECK_WINDOW`, `"2h"`) existence
  probe scoped to one monitor id, unrelated to the watermark/overlap ingest fetch above (STORY-070,
  see [[demo-engine]] and [[zone-rules]] for the probe's own use and the ZR-8 finding it fixed).
  Shares `query.py::_reject_dql_breaking_native_id` with `build_dql_query` above (the extracted
  validation both builders now call), so a `native_id` misconfiguration raises the same
  `InvalidNativeIdError` on both paths — before STORY-204, `composition/vendor_health.py`'s own
  copy of this builder validated nothing.

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
- As of sprint-62 it is also exercised **unmodified against a real socket**: the Grail demo engine
  (`tools/demo_engine/`, STORY-148) implements the async execute→poll wire protocol well enough that
  this exact factory, with its own default `httpx`, drives it end-to-end — see [[demo-engine]] for
  the wire contract, and for the hard limit that engine carries (it can emit `HEALTHY` rows and
  absence, nothing else, because `map_synthetic_status` raises on every unverified code).

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
- **Two dispatch entry points since STORY-190 (sprint 65).** `normalize_rows` is UNCHANGED and still
  STRICT — the first raising row aborts the whole list. Alongside it,
  `normalize_rows_lenient(rows, *, signal_key) -> NormalizationOutcome`
  (`dispatch.py::normalize_rows_lenient`) catches the three per-row failures
  **`ValueError`** and returns
  both the successfully-normalized `observations` (input order preserved) and a list of
  `RowNormalizationFailure` (`dispatch.py::RowNormalizationFailure`: the raw `row` dict plus a
  `reason` string). `fetch_observations` (`adapter.py::fetch_observations`) now uses the lenient path
  and returns `NormalizationOutcome`, not `list[SignalObservation]`.
- **The catch is `ValueError`, deliberately broad, and that width was earned.** The first
  implementation named exactly three classes, which closed the defect only for a MISSING field, an
  unmapped `event.type` and an unknown status. A field that is PRESENT BUT INVALID still escaped and
  still killed the whole cycle -- verified live during the sprint-65 quality review against the real
  captured fixture: an unparsable `timestamp` raises a bare `ValueError`, and a null
  `dt.entity.synthetic_location` raises pydantic's `ValidationError`. Both propagated out to
  `run_periodic`, leaving the watermark unadvanced -- precisely the defect this function exists to
  close, and a vendor shape change emitting a `null` location is a realistic trigger. All three named
  errors AND pydantic's `ValidationError` are `ValueError` subclasses, so `ValueError` is the exact
  net. It stays narrower than `Exception`, so a `TypeError`/`AttributeError` still surfaces loudly
  instead of being silently recorded as a bad vendor row (pinned by
  `test_normalize_rows_lenient_does_not_swallow_programming_errors`).
- **Why the strict function was kept rather than replaced:** it is the fail-loud unit, is called
  directly by eight tests, and its behaviour is itself the thing STORY-190's regression test pins.
  Both failure types are ADAPTER-LOCAL — `RowNormalizationFailure` carries a raw vendor row dict, so
  it deliberately does NOT live in `core/domain/`, and this adapter persists nothing: it returns
  values, and `composition` decides what to do with the failures (see
  [[ingest-service-and-pull-loop]]).

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
- **Live HTTP path (STORY-016b, REWRITTEN by STORY-177 sprint 65):**
  `map_synthetic_status(*, code, message)` (`health_mapping.py::map_synthetic_status`) resolves in
  THREE steps, in this order:
  1. the healthy OR-rule, first and unchanged — `code == "0"` **or** `message == "HEALTHY"` →
     `Health.UP` (an `or`, so either half alone suffices; pinned by
     `test_dynatrace_adapter.py::test_map_synthetic_status_message_only`, which asserts
     `code="123", message="HEALTHY"` is still `UP`);
  2. an EXACT `(code, message)` tuple lookup in `PROVISIONAL_STATUS_MAPPING` — two entries,
     `("1","UNHEALTHY") → Health.DOWN` and `("2","DEGRADED") → Health.DEGRADED` — logging a WARNING
     naming the code, the message and its unverified status;
  3. otherwise raise the named `UnknownVendorStatusError`
     (`health_mapping.py::UnknownVendorStatusError`).
  The tuple match is deliberately exact, never code-only, so a provisional entry cannot over-match a
  real vendor value. **The fail-loud property the original design existed to protect is intact:** any
  pair outside both rules still raises, naming the real code and message, so a genuine vendor failure
  code still surfaces to be read and mapped.
- **SUPERSEDED, kept so the change does not read as a regression:** this section previously said only
  the healthy value is mapped and "the real DOWN/DEGRADED code(s) are captured during the live
  verification (STORY-016b plan T6/AC6) and the mapping is extended THEN", with inventing failure
  codes "explicitly rejected at review". That reasoning was sound while a tenant existed. **The
  Dynatrace trial expired 2026-07-28, so the live verification it defers to CANNOT happen**, and the
  entire failure half of the business logic was unexercisable end to end. STORY-177 was the
  first-class reviewed decision to add a PROVISIONAL, explicitly-labelled mapping; STORY-154 replaces
  its contents with real codes once a tenant exists. The two provisional pairs remain **UNVERIFIED
  ASSUMPTIONS** — no Dynatrace failure code has ever been observed.
- **Legacy clickpath path:** `map_execution_outcome(outcome)` (`health_mapping.py::map_execution_outcome`,
  `success→UP`/`failure→DOWN`/`partial→DEGRADED`, raises `UnknownVendorOutcomeError`) is still used by
  `clickpath_normalizer` against the old `execution.outcome` field. Browser clickpath is out of the
  live HTTP scope (not in the live dispatch registry), so this path is retained but not exercised live.
- **STORY-201:** `normalize_clickpath_row` (`clickpath_normalizer.py::normalize_clickpath_row`) now
  reads `execution.outcome` via the shared `require_field` (`_assembly.py::require_field`), matching
  `http_normalizer.py`'s `result.status.code`/`result.status.message` pattern — a missing field raises
  the named `MalformedDqlRowError` (a `ValueError` subclass) instead of a bare `KeyError`. Pinned by
  `test_dynatrace_adapter.py::test_clickpath_normalizer_raises_malformed_for_missing_execution_outcome`.
  **This closes only the direct-call path.** `normalize_clickpath_row` is still not reachable through
  `dispatch.py`'s `_NORMALIZERS` (see above — clickpath's real `event.type` is unknown and unregistered),
  so the claim that a malformed clickpath row would now be caught by `normalize_rows_lenient`'s
  `except ValueError` net is an INFERENCE from the type relationship
  (`MalformedDqlRowError` < `ValueError`), not an end-to-end demonstration — no clickpath row can reach
  that dispatch path today to prove it directly.

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
- sprint-62 (compile pass, STORY-148): added one Fact to the `grail_executor.py` subsection and a
  cross-link to the new [[demo-engine]] article — `make_grail_executor` is now driven UNMODIFIED
  against a real socket by `tools/demo_engine/`, which is a materially stronger statement than
  "tested against fakes" and belongs where a reader of this article will look for it. **No file in
  this article's `code_refs` changed** (STORY-148's AC9 forbade touching `backend/src/`), so
  `verified_sha` deliberately stays `0da9568`: the new claim's own evidence lives in
  [[demo-engine]], verified at `64f680b`. Bumping this article's SHA would have implied a
  re-verification of the adapter that did not happen.
- sprint-63 (STORY-181): `query.py`'s dedupe comment corrected — it had cited a SQL
  `UNIQUE(observations.source_event_id)` constraint that never existed in this DynamoDB-backed
  system; the Fact above now names the real mechanism, the `EVT#.../DEDUPE` marker item. The
  claim itself (the two rows sharing `event.id` never collide) is unchanged. verified_sha ->
  b272c32.
- sprint-68 (STORY-204): `query.py` gained a SECOND DQL builder, `build_vendor_health_dql`,
  relocated here from `composition/vendor_health.py` (ZR-8 finding 2 — see [[zone-rules]]) so
  query-construction logic lives in exactly one adapter. `build_dql_query`'s own inline
  breaking-character check was extracted into a shared `_reject_dql_breaking_native_id` helper both
  builders now call — its behaviour, error type and error message are unchanged (proven by its
  existing tests passing without modification; `_DQL_BREAKING_CHARS`/`InvalidNativeIdError` are
  untouched). Added a new Fact for the relocated builder and its own two new tests
  (`test_build_vendor_health_dql_scopes_to_native_id_and_bounded_window`,
  `test_build_vendor_health_dql_rejects_native_id_with_dql_breaking_char`) in
  `test_dynatrace_adapter.py`, next to `build_dql_query`'s.
- sprint-68 (STORY-204 fix round): the sprint-68 entry above wrongly claimed "No other Fact in this
  article changed" while re-stamping `verified` over one that was already false — the breaking-char
  Fact above named only `"`, backslash, and a newline, omitting `\r`, the fourth member of
  `_DQL_BREAKING_CHARS` (`query.py::_DQL_BREAKING_CHARS`) that was already in the code at the
  STORY-204 relocation and stayed unlisted through it. Both spec and quality review independently
  caught this — a `verified` stamp over a known-false Fact is the forbidden fourth state (YourTeam
  core principle 5). Fixed the Fact to name all four characters and stated why `\r` matters on this
  Windows-developed repo. verified_sha -> e60d027.
- sprint-68 (STORY-204 fix round, second pass): `_HEALTH_CHECK_WINDOW` made public
  (`HEALTH_CHECK_WINDOW`, same fix round, unrelated minor — the only private-name import across a
  module/zone boundary in `backend/src`). The `build_vendor_health_dql` Fact above repointed to the
  new public name. verified_sha -> bfa5f77.
- sprint-68 (STORY-204 second fix round): the sprint-68 second-pass entry's "why `\r` matters" was
  itself FALSE — it asserted a CRLF-contaminated `native_id` in `config/apps/*.yaml` as the
  realistic trigger. Disproved end-to-end, twice (reviewer + independently): `load_config` reads
  via `Path.read_text()` (`composition/config.py::load_config`), which applies universal-newline
  translation before PyYAML ever sees the text, so CRLF line endings in the YAML file cannot
  reach `native_id` as a literal `\r`. Replaced with the verified trigger (an explicit `\r`
  escape inside a double-quoted YAML scalar) and the true justification (the constant guards
  against any breaking character regardless of provenance); the ruled-out CRLF path is stated
  explicitly, with the reason, so it is not re-derived. Also corrected the adjacent claim that the
  outcome "depends on which of the two builders" the character reaches first — in the loop
  process, `composition/run.py::main` always runs the vendor-health probe before
  `seed_topology_dynamo`/`build_live_loop`, so there is no dependency for that process. Also
  narrowed "the only private-name import" (line above) to the leading-underscore-*symbol* reading
  it actually holds under — `composition/app.py:224` imports the private *package*
  `src.api.v1._shared.errors` across the same kind of zone boundary, which is a private PACKAGE,
  not a private NAME. No file in this article's `code_refs` changed in this pass (prose-only
  correction); `verified_sha` is bumped below to this fix round's landing commit anyway, since the
  correction is itself the re-verification this article needed.
- sprint-71 (STORY-201): `clickpath_normalizer.py` bypassed `require_field` for `execution.outcome`,
  reading `row["execution.outcome"]` directly and raising a bare `KeyError` on a missing field
  instead of the named `MalformedDqlRowError`, against the article's own documented policy. Fixed to
  match `http_normalizer.py`'s pattern; added the Fact above, including the scope limit (the
  quarantine-net claim is an inference from `MalformedDqlRowError < ValueError`, not demonstrated,
  because clickpath is still unreachable through `dispatch.py::_NORMALIZERS`). No other Fact
  changed.
