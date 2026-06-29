# Sprint 22 — Plan

**Goal.** Close the live ingest gap surfaced by STORY-016b's AC6 run. The PO's monitor emits **two event
types per execution** — `http_monitor_execution` (the canonical per-run verdict) and `http_step_execution`
(the per-step row) — sharing the same `event.id` and `timestamp`. The dispatch registry only knew
`http_step_execution`, so the live loop crashed with `UnsupportedMonitorTypeError` on the monitor_execution
row; and normalizing both would collide on `UNIQUE(observations.source_event_id)`. Reconcile the adapter to
ingest **exactly one canonical observation per execution**, then re-run the loop against the live tenant.

**Single story: STORY-016c (3 pts)** — deliberate under-commit (velocity 5.0); focused single-fix
reconciliation sprint. Pipeline: `impl (Sonnet) + Opus spec & quality reviewers + DoD gate`.

## Baseline
- Branch `sprint-22` cut from `main` @ `654829c` (sprint-21 merged). `start_tag`: `sprint-22-start`.
- DB-gated gates via the shared throwaway-DB harness (`scripts/dev_db.py` / `migrated_db`).

## The ground truth (from the 2026-06-29 AC6 live run + re-probe — saved in memory `dynatrace-grail-real-schema`)
A single `fetch dt.synthetic.events | filter dt.synthetic.monitor.id == "HTTP_CHECK-DB5792CB88D14CF4"`
returns BOTH event types. The **canonical** `http_monitor_execution` record (HEALTHY):
```
timestamp                          2026-06-29T08:30:40.746000000Z   (9-digit ns precision)
event.id                           156345503298        (← the SAME id on the companion step row)
event.kind                         SYNTHETIC_EVENT
event.type                         http_monitor_execution
result.state                       SUCCESS             (monitor-execution-only field)
result.executed_steps_count        1                   (monitor-execution-only field)
dt.entity.http_check               HTTP_CHECK-DB5792CB88D14CF4   (monitor-execution-only field)
dt.synthetic.monitor.id            HTTP_CHECK-DB5792CB88D14CF4
dt.entity.synthetic_location       SYNTHETIC_LOCATION-000000000000005C
result.status.message              HEALTHY
result.status.code                 0
result.statistics.duration         755000000           (nanoseconds → 755 ms)
result.statistics.response_status_code   200
monitor.name                       TodoMVC Homepage Monitor
```
The companion `http_step_execution` row has the SAME `event.id` + `timestamp`, adds `step.name`,
`step.sequence_number`, `dt.entity.http_check_step`, `dt.synthetic.step.id`, and is what we DON'T want.

The async API + auth are unchanged from STORY-016b and already work (`query:execute` → 202 → poll
`query:poll` → SUCCEEDED → `result.records`; `Authorization: Api-Token <token>`; scopes
`storage:buckets:read storage:events:read`). The executor, normalizer body, `_assembly`, and health
mapping are all CORRECT for this row already — only the dispatch key and the query scope are wrong.

---

## Tasks (TDD; commit after each green; scoped staging — never `git add -A`)

### T1 — Record the canonical fixture  *(AC4)*
- Update `backend/tests/fixtures/dynatrace/grail_synthetic_events.json` so its `records` are real
  `http_monitor_execution` rows authored from the probe values above (≥2 records; keep the ns `timestamp`
  and ns `result.statistics.duration` verbatim so the precision-boundary path is exercised; include
  `result.state`). The two records must have DISTINCT `event.id` (they are distinct executions).
- If a test needs to demonstrate the step-row exclusion (T5/AC5), add a small sibling fixture (e.g.
  `grail_dual_event_types.json`) holding ONE execution as BOTH an `http_monitor_execution` row and its
  same-`event.id` `http_step_execution` companion. Implementer's call whether to keep the old
  `http_step_execution`-as-canonical fixture content anywhere — but NO test may still treat the step row as
  the ingested canonical observation.

### T2 — Query fetches only the canonical execution row  *(AC1)*
- `adapters/inbound/dynatrace/query.py::build_dql_query`: add a filter clause
  `event.type == "http_monitor_execution"` to the existing `dt.synthetic.monitor.id == "<native_id>"`
  scope (AND-joined, same `| filter` line is fine), keeping the optional `timestamp >= "<since>"` overlap
  lower bound and `sort timestamp asc`. The STORY-021 `InvalidNativeIdError` guard and the
  tz-aware-watermark rejection are UNCHANGED. Document in the builder that `http_monitor_execution` is the
  single live monitor type and that per-type parameterization is out of scope (future multi-type work).
- Tests `test_dynatrace_adapter.py`: extend the two query assertions
  (`test_build_dql_query_targets_real_object_and_filter_field`,
  `test_build_dql_query_with_watermark_adds_overlap_lower_bound`) to assert the emitted DQL contains
  `event.type == "http_monitor_execution"`. The naive-watermark + breaking-char rejection tests stay.

### T3 — Dispatch routes the canonical row  *(AC2, AC3)*
- `adapters/inbound/dynatrace/dispatch.py::_NORMALIZERS`: map `"http_monitor_execution" -> normalize_http_row`.
  Decide explicitly whether to KEEP `"http_step_execution"` in the registry: since the query now filters it
  out, production never dispatches it; prefer REMOVING it so the registry states intent (the canonical row
  is the monitor execution) — but if existing step-row tests are retained, keep the mapping and adjust the
  comment. Either way, an unmapped `event.type` still raises `UnsupportedMonitorTypeError` (fail-loud,
  defense-in-depth behind the query filter) and a row missing `event.type` still raises
  `MalformedDqlRowError`. Update the module docstring/comment to reflect the dual-event-type reality and the
  canonical choice.
- Tests `test_dynatrace_adapter.py`: a real-object test drives a recorded `http_monitor_execution` row
  through `normalize_rows` → asserts `SignalObservation(health=UP, latency_ms=755, location=SYNTHETIC_…,
  source_event_id="156345503298", source.native_id="HTTP_CHECK-DB5792CB88D14CF4", observed_at parsed)`.
  The `UnsupportedMonitorTypeError` test (unmapped type, e.g. `unsupported_monitor_type.json`) and the
  missing-`event.type` → `MalformedDqlRowError` test stay green (retargeted to the new fixture as needed).

### T4 — Reconcile the pull-loop tests  *(AC4)*
- `test_pull_loop.py` builds rows inline with `"event.type": "http_step_execution"` (lines ~52, ~315–335)
  and feeds them through the loop. Retarget these to `"http_monitor_execution"` (and any other fields that
  must match the canonical row) so the loop tests exercise the type production now ingests. No production
  pull-loop change is expected — this is fixture/row reconciliation only.
- `test_grail_executor.py` loads `grail_synthetic_events.json`; confirm it still passes against the
  canonical fixture (the executor is shape-agnostic — it returns `result.records` verbatim — so this is a
  consistency check, not a change).

### T5 — Demonstrate single-observation-per-execution  *(AC5)*
- A test that feeds a batch containing BOTH a `http_monitor_execution` row and its same-`event.id`
  `http_step_execution` companion (the T1 sibling fixture) and asserts exactly one observation results for
  that execution. Make the dedup MECHANISM explicit: the production path excludes the step row via the AC1
  query filter (a query-string assertion), so it is never dispatched — frame the test to show that, rather
  than relying on a DB unique-constraint catch. (If demonstrated purely at the dispatch layer, assert that
  feeding only the canonical row yields one observation and that the step companion is excluded by the
  query filter, citing T2.)

### T6 — Internal live verification  *(AC6, manual, PO-observed — closes STORY-016b's deferred AC6)*
Runbook (orchestrator + PO run this in the back half, after the gate + reviewers pass):
  1. `python scripts/dev_db.py up` → export both URLs; schema migrated by the helper.
  2. With only the two Dynatrace vars exported (sourced from `.env`), run `python -m src.composition.run`.
  3. Confirm NO `UnsupportedMonitorTypeError`; the loop completes a cycle and real observations land.
     Confirm via the API: `GET /api/v1/history?signal_key=http-check` returns rows for the live monitor
     (location `SYNTHETIC_LOCATION-…`, health up, latency ~hundreds of ms), OR query the `observations`
     table directly if the API isn't run.
  4. If a failing run can be induced (force the monitor down ≥ `major`=5 cycles × 120 s ≈ 10 min): the loop
     hits an unknown status → `UnknownVendorStatusError` naming the real failure `code`/`message`; READ it,
     add the DOWN (and DEGRADED if a partial code appears) mapping to `health_mapping.py`, commit, re-run.
     If a failing run can't be induced this sprint, note the failure mapping remains TBD (fail-loud holds).
  5. Confirm a degradation proposal appears at `GET /api/v1/approvals` (only if a failure was induced).
  6. Record the observed outcome (+ any failure mapping) in the review/retro.

---

## Conventions checklist (held at quality review — standing)
- **Docstrings** on every changed module/function citing the dossier § (dispatch §5, query §8).
- **Named domain errors** — `UnsupportedMonitorTypeError` (unmapped event.type), `MalformedDqlRowError`
  (missing required field) preserved; `UnknownVendorStatusError` only touched if a live failure is mapped.
- **Empty-input + precision-boundary tests** — the ns-timestamp and ns-duration cases remain in the
  canonical fixture (non-aligned boundary, 2026-06-25 agreement); empty `records` → `[]` still holds.
- **Real-object tests, no constructor patching** — normalize tests build real fixtures → real
  `SignalObservation` (2026-06-29 assembly-tests-build-real-objects agreement).
- **Frozen value types** — N/A (no new cross-field invariant this sprint).
- **Scoped staging; clean committed tree** — commit any `ruff format` reflow in the SAME step it arises
  (2026-06-29 clean-committed-tree agreement). Never `git add -A`.
- **Command-sync** — no command change this sprint; CLAUDE.md needs no edit (the run command + the two
  Dynatrace vars are already documented).
- **Wiki blast-radius** — at DoD, mechanical sweep over all `docs/scrum/wiki/*.md`; expected drift:
  `dynatrace-adapter` (dispatch registry + query filter — the canonical event.type). Re-verify/update every
  article the `git diff <verified_sha>..HEAD -- <code_refs>` sweep reports.

## DoD gate (all six exit 0 on a CLEAN committed tree)
`pytest` · `lint-imports` (stays 5) · `python scripts/check_fk_direction.py` · `alembic upgrade head`
(no new migration) · `ruff check` · `ruff format --check`.

## Guardrails for the implementer
Build to THIS plan + the STORY-016c AC + the dossier + the saved real-schema reference (`dynatrace-grail-real-schema`,
CORRECTION/EXPANSION section) — never to chat history or the OLD `http_step_execution`-as-canonical shape.
The fix is small: the executor, normalizer body, `_assembly`, and health mapping already handle this row —
DO NOT rewrite them; change only the dispatch key + the query filter, then reconcile fixtures/tests. Do NOT
write `.scrum/` board state. Do NOT run the reviewers or merge. Stop-and-report on genuine ambiguity or a
3× effort overrun.
