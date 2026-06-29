---
id: STORY-016b
title: Live Dynatrace reconciliation — real Grail schema + async query, verified internally
type: feature
---

## Context
Spec: dossier §5/§7/§8. Split-child of STORY-016. STORY-016 shipped a gate-green live loop built to
ILLUSTRATIVE Dynatrace field names; a read-only live probe of the PO's tenant
(`https://bqm75769.apps.dynatrace.com`, monitor `HTTP_CHECK-DB5792CB88D14CF4` = "TodoMVC Homepage
Monitor", 2026-06-29) proved the Dynatrace creds WORK but the ingest code does not match reality. This
story reconciles the ingest path to the real Grail schema and **verifies the pipeline end to end
INTERNALLY** (real monitor → observations → pipeline → proposal via the API). **Statuspage is out of
scope** (PO decision): the publish side is already coded + fixture-tested, so once a valid Statuspage
key exists it follows — the internal verification is what de-risks the thread.

## What the live probe found (the three real gaps — see the saved schema reference)
1. **Wrong data object.** `fetch dt.synthetic.executions` returns 400 "isn't a valid data object". The
   real object is **`dt.synthetic.events`**. The filter field is **`dt.synthetic.monitor.id`** (not
   `synthetic_test.id`).
2. **The Grail query API is ASYNCHRONOUS.** `POST …/query:execute` returns HTTP **202**
   `{"state":"RUNNING","requestToken":"…","ttlSeconds":~400}`. You must poll
   `GET …/query:poll?request-token=…` until `state=="SUCCEEDED"`, then read `result.records`. The current
   `grail_executor` treats 202 as success, finds no `records`, and silently returns `[]`.
3. **The field names are entirely different**, and timestamps are 9-digit **nanosecond** precision
   (`2026-06-29T06:45:40.742000000Z`) which breaks `datetime.fromisoformat`. Real → canonical:
   - `timestamp` (ns) → `observed_at` (truncate fractional to µs before parse).
   - `event.id` → `source_event_id`.
   - `dt.synthetic.monitor.id` → `Provenance.native_id`.
   - `result.status.message`=`HEALTHY` / `result.status.code`=`"0"` → `Health` (NOT
     `execution.outcome` success/failure/partial). Only the healthy value is known; the failure value is
     captured during internal verification (T6).
   - `result.statistics.duration` = nanoseconds (string) → `latency_ms` (÷ 1e6).
   - `dt.entity.synthetic_location` = a location ENTITY id (e.g. `SYNTHETIC_LOCATION-…000005C`) →
     `location` (use the id as-is; display-name resolution is out of scope — needs `storage:entities:read`).
   - dispatch: real rows carry `event.type`=`http_step_execution` / `event.kind`=`SYNTHETIC_EVENT`, NO
     `synthetic_test.type`. Dispatch must key on `event.type`.

## Acceptance Criteria
- [ ] **AC1 — Query targets the real object.** `build_dql_query` fetches `dt.synthetic.events` and filters
      `dt.synthetic.monitor.id == "<native_id>"` (watermark/overlap lower-bound on `timestamp` unchanged).
      The `native_id` DQL-injection guard (STORY-021) and tz-aware-watermark rule still hold. Tests updated.
- [ ] **AC2 — Executor polls the async query to completion.** `make_grail_executor` POSTs `query:execute`;
      on a 202 + `requestToken` it polls `query:poll?request-token=…` until `state` is terminal, returns
      `result.records` on `SUCCEEDED` (`[]` when empty), and raises the named `GrailQueryError` on a FAILED/
      CANCELLED state, a non-2xx, or a poll timeout (bounded retries). A synchronous 200-with-records
      response is still handled. Driven by a fake transport simulating execute→202→poll→SUCCEEDED — NO live
      call in any test.
- [ ] **AC3 — Normalizer maps the real fields.** The HTTP normalizer + `_assembly` produce a correct
      `SignalObservation` from a REAL `dt.synthetic.events` row: ns-timestamp parsed (µs-truncated),
      `dt.synthetic.monitor.id`→native_id, `result.statistics.duration` ns→`latency_ms` ms,
      `dt.entity.synthetic_location`→location, health via the new status mapping. A missing required field
      still raises `MalformedDqlRowError`. Driven by a NEW recorded fixture authored from the live probe
      (`backend/tests/fixtures/dynatrace/grail_synthetic_events.json`), including the ns-timestamp and
      ns-duration cases (non-aligned/precision boundary per the working agreement).
- [ ] **AC4 — Health maps from the real status, fail-loud on unknown.** A new explicit mapping
      (`result.status.code`/`message` → `Health`) replaces `execution.outcome`: `code "0"` / `HEALTHY` →
      `UP`; an unrecognized value raises a named error (not a silent default) so a surprise surfaces. The
      failure/degraded values are filled in from the live observation in T6 and committed.
- [ ] **AC5 — Dynatrace-only live driver (Statuspage optional).** `load_live_secrets` requires only the
      two Dynatrace vars; the Statuspage vars are optional. `build_live_loop` wires the real Statuspage
      chain only when the Statuspage secrets + mapping are present, else injects a no-op
      `LoggingPublisher` (a `StatusPublisherPort` that logs and does nothing) so the loop runs
      Dynatrace-only. Fake-backed test asserts: Statuspage-absent → `DecideService` gets a
      `LoggingPublisher`; Statuspage-present → the existing `BestEffortPublisher(RecordingPublisher(
      StatuspagePublisher))` chain (STORY-016 test still green). No publication rows are written on the
      no-op path.
- [ ] **AC6 — Internal end-to-end verification (manual, the headline acceptance).** Runbook in plan.md:
      run the loop against the live monitor + a throwaway Postgres; confirm real observations land in
      `observations` (visible via `GET /api/v1/history`), then force the monitor to fail → confirm a
      degradation proposal appears at `GET /api/v1/approvals`. Capture the real failure
      `result.status.code`/`message` and commit it into the AC4 mapping. PO-observed; recorded in the retro.

## Out of scope (explicit)
- Live Statuspage publish/observation (deferred until a valid `STATUSPAGE_API_KEY` exists; the chain is
  already coded + fixture-tested — "external is bound to work" once the key is fixed).
- Synthetic-location display-name resolution (needs `storage:entities:read`); the entity id is used as
  `location`.
- Browser-clickpath dispatch under the real `event.type` (only the HTTP monitor is live).

## History
- 2026-06-29: created as a split-child of STORY-016 after the live probe proved the Dynatrace creds work
  but the ingest code was built to placeholder field names. Scoped for Sprint 21; Statuspage excluded by
  PO decision ("verify internally; external is bound to work"). 5 pts.
