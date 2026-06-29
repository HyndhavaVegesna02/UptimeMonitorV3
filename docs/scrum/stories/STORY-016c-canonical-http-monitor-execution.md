---
id: STORY-016c
title: Live reconciliation — dispatch + query the canonical http_monitor_execution row
type: feature
---

## Context
Spec: dossier §5/§8. Split-child of STORY-016, follow-up to STORY-016b. STORY-016b's AC6 (the manual
internal live verification) was run on 2026-06-29 against the PO's real tenant
(`https://bqm75769.apps.dynatrace.com`, monitor `HTTP_CHECK-DB5792CB88D14CF4` = "TodoMVC Homepage
Monitor"). It proved the executor / async-poll / field-remap path works against live Grail — but the loop
crashed at normalization:

```
src.adapters.inbound.dynatrace.dispatch.UnsupportedMonitorTypeError:
  unsupported Dynatrace event.type: 'http_monitor_execution'
```

A read-only probe (50 recent records) showed the monitor emits **two event types per execution**:

| event.type               | count | what it is                                                              |
| ------------------------ | ----- | ----------------------------------------------------------------------- |
| `http_monitor_execution` | 26    | the per-run overall verdict — the canonical "one observation per execution" (dossier §5) |
| `http_step_execution`    | 24    | the per-step row (1:1 here — single-step monitor)                       |

Two problems, one root cause: (a) `dispatch.py::_NORMALIZERS` registers only `http_step_execution`, so a
`http_monitor_execution` row raises `UnsupportedMonitorTypeError`; and (b) the monitor-execution row and
its companion step row **share the same `event.id` and `timestamp`**, so normalizing both would collide
on the `UNIQUE(observations.source_event_id)` index — we must ingest exactly one canonical row per
execution. STORY-016b built the normalizer/assembly against the step row; the `http_monitor_execution`
row carries every field the normalizer reads (`result.status.message`/`code`, `result.statistics.duration`,
`dt.synthetic.monitor.id`, `dt.entity.synthetic_location`, `event.id`, `timestamp`) plus extras
(`result.state`, `result.executed_steps_count`, `dt.entity.http_check`), so no normalizer-body change is
needed — only the dispatch key and the query scope.

The real shape is saved in memory `dynatrace-grail-real-schema` (CORRECTION/EXPANSION section, 2026-06-29).

## Acceptance Criteria
- [ ] **AC1 — Query fetches only the canonical execution row.** `build_dql_query` adds an
      `event.type == "http_monitor_execution"` filter clause (alongside the existing
      `dt.synthetic.monitor.id` scope and the optional watermark/overlap lower bound on `timestamp`). This
      excludes the duplicate `http_step_execution` companion row at the source, so no two observations ever
      share an `event.id`. The STORY-021 native_id injection guard and the tz-aware-watermark rule still
      hold. A unit test asserts the emitted DQL contains the `event.type == "http_monitor_execution"`
      filter (both the no-watermark and with-watermark forms). The HTTP-specific event.type is documented
      in the builder as the single live monitor type; parameterizing it for future monitor types is
      explicitly out of scope.
- [ ] **AC2 — Dispatch routes the canonical row.** `dispatch.py::_NORMALIZERS` maps
      `http_monitor_execution` → `normalize_http_row`. A real-object test drives a recorded
      `http_monitor_execution` row through `normalize_rows` and asserts a correct `SignalObservation`:
      `health == UP` (from `result.status.message == "HEALTHY"` / `code == "0"`), `latency_ms` from
      `result.statistics.duration` (ns → ms), `location` = the `dt.entity.synthetic_location` id,
      `source_event_id` = `event.id`, `Provenance.native_id` = `dt.synthetic.monitor.id`.
- [ ] **AC3 — Fail-loud contract preserved.** An `event.type` with no registered normalizer still raises
      `UnsupportedMonitorTypeError` (NOT a silent drop), and a row missing `event.type` still raises
      `MalformedDqlRowError` — the STORY-016b/AC4 fail-loud behavior is defense-in-depth behind the new
      query filter, not weakened. Existing tests asserting this stay green (retargeted to the new fixture
      where they read `event.type`).
- [ ] **AC4 — Recorded fixture reconciled to reality.** `grail_synthetic_events.json` (or a clearly named
      sibling) carries the REAL `http_monitor_execution` record captured from the live probe, including
      `result.state`, the ns-`timestamp`, and the ns-`result.statistics.duration`. The existing
      consumers — `test_dynatrace_adapter.py`, `test_pull_loop.py`, `test_grail_executor.py` — are
      reconciled to the canonical type and stay green. Whether the legacy `http_step_execution` step row is
      retained as a separate fixture (for a "the query filter excludes it" demonstration) or dropped is the
      implementer's call, as long as no test still treats the step row as the ingested canonical row.
- [ ] **AC5 — No duplicate observation per execution (demonstrated).** A test feeds a batch containing
      BOTH a `http_monitor_execution` row and its same-`event.id` `http_step_execution` companion through
      the normalize path and asserts exactly one observation is produced for that execution — i.e. the
      step row is not independently ingested (because the query filter, asserted in AC1, excludes it; the
      test makes the dedup mechanism explicit rather than implicit).
- [ ] **AC6 — Internal live verification (manual, PO-observed; closes STORY-016b's deferred AC6).**
      Runbook in plan.md: `python -m src.composition.run` against the live monitor + a throwaway Postgres
      ingests real observations with NO `UnsupportedMonitorTypeError`; confirm rows land in `observations`
      (via `GET /api/v1/history`). If a failing run can be induced, capture the real failure
      `result.status.code`/`message` and commit it into the health mapping (otherwise note it remains TBD,
      preserving fail-loud). PO-observed; recorded in the review/retro.

## Out of scope (explicit)
- Live Statuspage publish (unchanged from STORY-016b — chain coded + fixture-tested, follows a valid key).
- Parameterizing the fetched `event.type` per monitor type (only the HTTP monitor is live; clickpath/
  browser dispatch under their real `event.type` remains future work).
- Synthetic-location display-name resolution (needs `storage:entities:read`; the entity id is the location).

## History
- 2026-06-29: created as a split-child of STORY-016 after STORY-016b's AC6 live run surfaced the
  `http_monitor_execution` dispatch gap and the shared-`event.id` duplicate-row hazard. 3 pts.
