---
title: Zone 3 — the Dynatrace inbound adapter (DQL → canonical observations)
code_refs: [backend/src/adapters/inbound/dynatrace/, backend/tests/test_dynatrace_adapter.py, backend/tests/fixtures/dynatrace/]
verified_sha: 40ed985
verified_sprint: sprint-4
status: verified          # verified | stale | archived
---

## Facts (verified against code)

The first inbound adapter (STORY-008, Zone 3, dossier §5/§7/§8). It queries Dynatrace
synthetic monitor results via DQL and normalizes each location execution into a canonical
`SignalObservation` (see [[canonical-types-and-ports]]). Vendor specifics are fully
contained here; `lint-imports` proves the core stays untouched (see [[architecture-boundary]]).

### The pull-cycle entry point
- `fetch_observations(*, signal_key, native_id, watermark, executor, overlap=DEFAULT_OVERLAP)`
  (`adapter.py:25`) is what STORY-009's pull loop will call. It builds the DQL query, runs it
  through the injected `executor`, and dispatches every row to its normalizer — returning a
  flat `list[SignalObservation]`, one per location execution, never aggregated (`adapter.py:43-45`).
- `DEFAULT_OVERLAP = timedelta(minutes=5)` (`adapter.py:22`) — the dossier §8 overlap window.

### DQL query builder + the executor seam (`query.py`)
- `build_dql_query(*, native_id, watermark, overlap)` (`query.py:26`) is a pure function. It
  always scopes to `synthetic_test.id == "<native_id>"`; when `watermark` is set it adds a
  lower bound at `watermark - overlap` (never the bare watermark, so late-landing rows are not
  missed — dossier §8); when `watermark is None` (never ingested) it adds no time bound and the
  first pull reads everything (`query.py:43-60`).
- `watermark` must be tz-aware UTC — a naive datetime is rejected (`query.py:43-46`), mirroring
  the core's own `observed_at` validator (`core/domain/signal.py:77-88`).
- `native_id` is interpolated unescaped into the query string (`query.py:48-51`); a comment
  documents the trusted-input assumption (vendor config id, read-only Grail fetch — no injection
  vector).
- `Executor = Callable[[str], list[dict]]` (`query.py:23`) is the injected live-DQL seam.
  Production (composition root) injects a real HTTP-backed one; **every test injects a fake** —
  no live Dynatrace call is ever made in a test (working agreement: pure core, mockable edges).
  No concrete network executor exists yet (deferred to STORY-009 wiring).

### Normalizer dispatch (`dispatch.py`) — the additive seam
- `_NORMALIZERS` (`dispatch.py:24-27`) maps a vendor `synthetic_test.type` string to a normalizer:
  `"HTTP_CHECK" -> normalize_http_row`, `"BROWSER_CLICKPATH" -> normalize_clickpath_row`. Adding
  a future type (single-browser, NAM) is one registry entry + one normalizer module — no existing
  normalizer or call site changes (AC5).
- `normalize_row` raises `UnsupportedMonitorTypeError` (`dispatch.py:30,44-50`) for any unmapped
  type rather than mis-normalizing. `normalize_rows` (`dispatch.py:54`) maps it over a sequence,
  one observation per row, in input order, mixed monitor types/locations normalized independently.

### Per-type normalizers + shared assembly
- `normalize_http_row` (`http_normalizer.py:18`, `NATIVE_KIND="http"`) and
  `normalize_clickpath_row` (`clickpath_normalizer.py:21`, `NATIVE_KIND="clickpath"`,
  optional `raw_ref`) each compute their own `Health` then delegate to the shared assembler.
- The clickpath normalizer reads ONLY the monitor-level `execution.outcome` that Dynatrace
  already collapsed the per-step journey into; it ignores the `steps` array entirely — step
  detail is never modelled on the canonical shape (`clickpath_normalizer.py:1-11`, AC3).
- `assemble_observation(row, *, signal_key, health, native_kind, raw_ref=None)` (`_assembly.py:20`)
  is the single home of the `timestamp` parse (`datetime.fromisoformat(row["timestamp"].replace("Z","+00:00"))`)
  and the `SignalObservation`/`Provenance` construction (`_assembly.py:38-52`). Extracted in
  STORY-008 fix loop 1 to kill duplication between the two normalizers. The vendor monitor type
  lives only in `Provenance.native_kind`; `system="dynatrace"`, `native_id=row["synthetic_test.id"]`.
- Row field shape (the fixtures): `timestamp`, `event.id` (→ `source_event_id`),
  `synthetic_test.id` (→ `native_id`), `synthetic_test.type` (dispatch key),
  `synthetic_location.name` (→ `location`), `execution.outcome` (→ health),
  `request.response_time_ms` (→ optional `latency_ms`), and clickpath's unread `steps`.

### Health mapping (`health_mapping.py`) — the only place vendor outcome words are read
- `map_execution_outcome(outcome)` (`health_mapping.py:25`) is the single explicit, unit-tested
  translation: `success→UP`, `failure→DOWN`, `partial→DEGRADED` (`health_mapping.py:14-18`). It is
  total over the three documented outcomes and raises `UnknownVendorOutcomeError`
  (`health_mapping.py:21,33-37`) on anything else — a vendor change surfaces immediately rather
  than silently mis-mapping.

### Tests + fixtures
- `backend/tests/test_dynatrace_adapter.py` (20 tests) runs entirely off committed JSON fixtures
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
  fix-loop-1 shared-assembly extraction. Verified at 834b90c.
