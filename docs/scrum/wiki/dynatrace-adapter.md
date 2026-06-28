---
title: Zone 3 — the Dynatrace inbound adapter (DQL → canonical observations)
code_refs: [backend/src/adapters/inbound/dynatrace/__init__.py, backend/src/adapters/inbound/dynatrace/_assembly.py, backend/src/adapters/inbound/dynatrace/adapter.py, backend/src/adapters/inbound/dynatrace/clickpath_normalizer.py, backend/src/adapters/inbound/dynatrace/dispatch.py, backend/src/adapters/inbound/dynatrace/health_mapping.py, backend/src/adapters/inbound/dynatrace/http_normalizer.py, backend/src/adapters/inbound/dynatrace/query.py, backend/src/core/domain/signal.py, backend/tests/test_dynatrace_adapter.py, backend/tests/fixtures/dynatrace/clickpath_multi_location.json, backend/tests/fixtures/dynatrace/http_multi_location.json, backend/tests/fixtures/dynatrace/mixed_monitor_types.json, backend/tests/fixtures/dynatrace/unsupported_monitor_type.json]
verified_sha: 19eefc8
verified_sprint: sprint-18
status: verified          # verified | stale | archived
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
- `build_dql_query(*, native_id, watermark, overlap)` (`query.py::build_dql_query`) is a pure function. It
  always scopes to `synthetic_test.id == "<native_id>"`; when `watermark` is set it adds a
  lower bound at `watermark - overlap` (never the bare watermark, so late-landing rows are not
  missed — dossier §8); when `watermark is None` (never ingested) it adds no time bound and the
  first pull reads everything (`query.py::build_dql_query`).
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
  No concrete network executor exists yet (deferred to STORY-009 wiring).

### Normalizer dispatch (`dispatch.py`) — the additive seam
- `_NORMALIZERS` (`dispatch.py::_NORMALIZERS`) maps a vendor `synthetic_test.type` string to a normalizer:
  `"HTTP_CHECK" -> normalize_http_row`, `"BROWSER_CLICKPATH" -> normalize_clickpath_row`. Adding
  a future type (single-browser, NAM) is one registry entry + one normalizer module — no existing
  normalizer or call site changes (AC5).
- `normalize_row` raises `UnsupportedMonitorTypeError` (`dispatch.py::UnsupportedMonitorTypeError` and `dispatch.py::normalize_row`) for any unmapped
  type rather than mis-normalizing. `normalize_rows` (`dispatch.py::normalize_rows`) maps it over a sequence,
  one observation per row, in input order, mixed monitor types/locations normalized independently.

### Per-type normalizers + shared assembly
- `normalize_http_row` (`http_normalizer.py::normalize_http_row`, `NATIVE_KIND="http"`) and
  `normalize_clickpath_row` (`clickpath_normalizer.py::normalize_clickpath_row`, `NATIVE_KIND="clickpath"`,
  optional `raw_ref`) each compute their own `Health` then delegate to the shared assembler.
- The clickpath normalizer reads ONLY the monitor-level `execution.outcome` that Dynatrace
  already collapsed the per-step journey into; it ignores the `steps` array entirely — step
  detail is never modelled on the canonical shape (`clickpath_normalizer.py` ("Browser-clickpath synthetic monitor normalizer"), AC3).
- `assemble_observation(row, *, signal_key, health, native_kind, raw_ref=None)` (`_assembly.py::assemble_observation`)
  is the single home of the `timestamp` parse (`datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))`)
  and the `SignalObservation`/`Provenance` construction (`_assembly.py::assemble_observation`). Extracted in
  STORY-008 fix loop 1 to kill duplication between the two normalizers. The vendor monitor type
  lives only in `Provenance.native_kind`; `system="dynatrace"`, `native_id=row["synthetic_test.id"]`.
- Row field shape (the fixtures): `timestamp`, `event.id` (→ `source_event_id`),
  `synthetic_test.id` (→ `native_id`), `synthetic_test.type` (dispatch key),
  `synthetic_location.name` (→ `location`), `execution.outcome` (→ health),
  `request.response_time_ms` (→ optional `latency_ms`), and clickpath's unread `steps`.
- A missing REQUIRED field surfaces as a named `MalformedDqlRowError` (`_assembly.py::MalformedDqlRowError`), not a
  bare `KeyError` (STORY-020). Both `dispatch.normalize_row` (the `synthetic_test.type` dispatch
  key) and `assemble_observation` (the other four required fields) read through one
  `require_field(row, name)` helper (`_assembly.py::require_field`) so the error message is uniform.
  `request.response_time_ms` stays optional (read via `.get`) — its absence is NOT malformed.

### Health mapping (`health_mapping.py`) — the only place vendor outcome words are read
- `map_execution_outcome(outcome)` (`health_mapping.py::map_execution_outcome`) is the single explicit, unit-tested
  translation: `success→UP`, `failure→DOWN`, `partial→DEGRADED` (`health_mapping.py` ("outcome mapping")). It is
  total over the three documented outcomes and raises `UnknownVendorOutcomeError`
  (`health_mapping.py::UnknownVendorOutcomeError`) on anything else — a vendor change surfaces immediately rather
  than silently mis-mapping.

### Tests + fixtures
- `backend/tests/test_dynatrace_adapter.py` (22 tests) runs entirely off committed JSON fixtures
  under `backend/tests/fixtures/dynatrace/` (`http_multi_location.json`,
  `clickpath_multi_location.json`, `mixed_monitor_types.json`, `unsupported_monitor_type.json`).
  No real recorded DQL exists yet (no live Dynatrace this sprint) — fixtures are representative,
  authored from the dossier §8 row shape (sanctioned by the recorded-fixtures working agreement).

## Inference (synthesis, not verified)
- The `synthetic_test.type` registry values (`HTTP_CHECK`, `BROWSER_CLICKPATH`) and the exact DQL
  field names are representative; the real Grail/DQL identifiers should be reconciled against a
  live Dynatrace tenant when credentials exist (the implementer flagged the DQL string syntax as
  illustrative). The canonical output contract is stable regardless.

## History
- sprint-4: created (STORY-008). Documents the Dynatrace inbound adapter as built + the STORY-008
  fix-loop-1 shared-assembly extraction. Verified at 834b90c (re-stamped to 40ed985 at merge).
- sprint-5: STORY-020 — required DQL fields now raise the named `MalformedDqlRowError` via a shared
  `require_field` helper (replacing bare `KeyError`). Re-verified at d3a864d.
- sprint-6: STORY-021 — `build_dql_query` now rejects a `native_id` containing a DQL-breaking
  character (`"`, backslash, newline) via the named `InvalidNativeIdError`, instead of silently
  interpolating it unescaped. Re-verified at ae5f880.
