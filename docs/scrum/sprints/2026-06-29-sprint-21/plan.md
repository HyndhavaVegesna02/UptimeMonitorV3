# Sprint 21 — Plan

**Goal.** Reconcile the Dynatrace ingest path to the PO's REAL Grail schema (proven by a live probe) and
**verify the pipeline end to end internally** (real monitor → observations → pipeline → proposal via the
API). **Statuspage is out of scope** — the publish chain is coded + fixture-tested; once a valid key
exists it follows. Every mechanical test stays green via a NEW recorded fixture authored from the live
probe; the internal verification (AC6) is a manual PO-observed step.

**Single story: STORY-016b (5 pts)** — top of range (velocity last-3 = 5,5,5 → 5.0). Pipeline:
`gate + Opus spec & quality reviewers`.

## Baseline
- Branch `sprint-21` cut from `main` @ `7ea535d`. `start_tag`: `sprint-21-start` (set at lock).
- DB-gated gates via the shared throwaway-DB harness (`scripts/dev_db.py` / `migrated_db`).

## The ground truth (from the 2026-06-29 live probe — saved in memory `dynatrace-grail-real-schema`)
A real `dt.synthetic.events` record for `HTTP_CHECK-DB5792CB88D14CF4` (HEALTHY):
```
timestamp                          2026-06-29T06:45:40.742000000Z   (9-digit ns precision!)
event.id                           156340723200
event.kind                         SYNTHETIC_EVENT
event.type                         http_step_execution
dt.synthetic.monitor.id            HTTP_CHECK-DB5792CB88D14CF4
dt.entity.synthetic_location       SYNTHETIC_LOCATION-000000000000005C
result.status.message              HEALTHY
result.status.code                 0
result.statistics.duration         787000000        (nanoseconds → 787 ms)
result.statistics.response_status_code   200
monitor.name                       TodoMVC Homepage Monitor
```
Async API: `POST {env_url}/platform/storage/query/v1/query:execute` → `202 {"state":"RUNNING",
"requestToken":"…","ttlSeconds":~400}`; then `GET {env_url}/platform/storage/query/v1/query:poll?
request-token=…` → `{"state":"SUCCEEDED","result":{"records":[…]}}` (states also: RUNNING / FAILED /
CANCELLED / NOT_STARTED). Auth header `Authorization: Api-Token <token>` (works; scopes
`storage:buckets:read storage:events:read` are sufficient).

---

## Tasks (TDD; commit after each green; scoped staging — never `git add -A`)

### T1 — Record a real fixture  *(supports AC3)*
- `backend/tests/fixtures/dynatrace/grail_synthetic_events.json` — a `result.records` array with 2-3
  records authored from the probe values above (one HEALTHY; include the ns timestamp + ns duration
  verbatim so the precision-boundary path is exercised). This is the new representative fixture; the old
  `http_multi_location.json` shape is retired for the live path (keep the file if other tests use it, but
  the live normalizer tests use the new one).

### T2 — Query targets the real data object  *(AC1)*
- `adapters/inbound/dynatrace/query.py::build_dql_query`: `fetch dt.synthetic.events`; filter
  `dt.synthetic.monitor.id == "<native_id>"`; keep the `timestamp >= "<since>"` overlap lower bound and
  `sort timestamp asc`. Keep the `InvalidNativeIdError` guard + the tz-aware-watermark rejection. Update
  `test_dynatrace_adapter.py` query assertions.

### T3 — Executor polls the async query  *(AC2)*
- `adapters/inbound/dynatrace/grail_executor.py::make_grail_executor`: add an injected poll seam
  (`http_get=httpx.get` alongside `http_post`). Flow: POST execute → if 200 with `records`/`result.records`,
  return them (sync fallback); if 202 with `requestToken`, poll
  `{env_url}/platform/storage/query/v1/query:poll` with `params={"request-token": token}` until `state`
  is terminal — `SUCCEEDED` → return `result.records` (`[]` if absent); `FAILED`/`CANCELLED` → raise
  `GrailQueryError` (include state + message); bounded poll attempts (e.g. 30 × short sleep, configurable)
  → raise `GrailQueryError` on exhaustion. Non-2xx on execute or poll → `GrailQueryError` (as today).
  Keep the seam returning `list[dict]`; never leak `httpx.Response`.
- Tests `test_grail_executor.py`: fake `http_post` returns 202+token, fake `http_get` returns RUNNING
  once then SUCCEEDED+records → assert the records flow through and that `normalize_rows` accepts them;
  FAILED state → `GrailQueryError`; poll-exhaustion → `GrailQueryError`; sync-200 fallback still works;
  empty records → `[]`. NO live call. (Use an injected sleep/no-op so tests don't actually wait.)

### T4 — Normalizer + assembly map the real fields  *(AC3)*
- `adapters/inbound/dynatrace/dispatch.py`: dispatch on `event.type` (real key), mapping
  `"http_step_execution" -> normalize_http_row`. Unmapped `event.type` → `UnsupportedMonitorTypeError`.
  (Clickpath's real `event.type` is unknown/out of scope — leave a comment; do not guess.)
- `_assembly.py::assemble_observation`: parse the ns timestamp safely — truncate fractional seconds to 6
  digits before `datetime.fromisoformat` (e.g. regex/split on `.`, keep ≤6 digits, re-append `+00:00`),
  so `…742000000Z` parses. Map: `event.id`→source_event_id, `dt.synthetic.monitor.id`→
  `Provenance.native_id`, `dt.entity.synthetic_location`→`location`,
  `result.statistics.duration` (ns string)→`latency_ms` (int(ns)//1_000_000, optional via `.get`).
  Required fields that raise `MalformedDqlRowError` if absent: `timestamp`, `event.id`,
  `dt.synthetic.monitor.id`, `event.type`, `dt.entity.synthetic_location`.
- `http_normalizer.py::normalize_http_row`: health from the new mapping (T5) reading
  `result.status.code`/`result.status.message`.
- Tests `test_dynatrace_adapter.py`: drive the new fixture end to end (row → `SignalObservation` with the
  right native_id, location, latency_ms=787, observed_at parsed, health UP); missing-field → named error.

### T5 — Health maps from the real status (fail-loud)  *(AC4)*
- Replace/extend `health_mapping.py`: `map_synthetic_status(*, code: str, message: str) -> Health` —
  `code == "0"` (or `message == "HEALTHY"`) → `Health.UP`; unrecognized → a named error
  (`UnknownVendorStatusError`), NOT a silent default. Seed only the known-good value now; the
  failure/degraded mapping is captured live in T6 and committed in this story. Keep the old
  `map_execution_outcome` only if still referenced; otherwise retire it with its tests.
- Tests: HEALTHY/0 → UP; an unknown code/message → raises the named error (both the rejected and the
  valid shape, per the value-type agreement).

### T6 — Dynatrace-only live driver + the internal verification  *(AC5, AC6)*
- `composition/settings.py`: `LiveSecrets` Statuspage fields become `str | None`; `load_live_secrets()`
  requires only `DYNATRACE_ENV_URL` + `DYNATRACE_API_TOKEN` (named error if either missing); Statuspage
  vars are read if present, else `None`.
- `composition/publish_helper.py`: add `LoggingPublisher(StatusPublisherPort)` — logs the change and does
  nothing (module docstring cites §12; it is the no-op publisher for the Statuspage-absent path).
- `composition/run.py::build_live_loop`: if `secrets.statuspage_*` AND `config.statuspage_mapping()` are
  present → the existing `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))` chain; else →
  `LoggingPublisher()` directly (no Recording, so no publication rows on the no-op path). `DecideService`
  takes whichever.
- Tests `test_run_live_loop.py`: Statuspage-absent → `decide_service._publisher` is `LoggingPublisher`
  and no `RecordingPublisher` is constructed; Statuspage-present → the STORY-016 chain assertion still
  holds (build REAL objects — do NOT patch the constructors under assembly; 2026-06-29 agreement).
- **Internal verification runbook (AC6, manual):**
  1. `python scripts/dev_db.py up` → export both URLs; `alembic upgrade head`.
  2. Run the API (`uvicorn` over `create_app`) + the loop (`python -m src.composition.run`) on that DB,
     with only the two Dynatrace vars in `.env`.
  3. Confirm real observations land: `GET /api/v1/history?signal_key=http-check` returns rows for the
     live monitor (location `SYNTHETIC_LOCATION-…`, health up, latency ~hundreds of ms).
  4. Force the monitor to fail in Dynatrace (≥ `major`=5 cycles × 120 s ≈ 10 min). The loop will hit an
     unknown status → `UnknownVendorStatusError` naming the real failure `code`/`message`; READ it, add
     the mapping (DOWN, and DEGRADED if a partial code appears), commit, re-run.
  5. Confirm a degradation proposal appears: `GET /api/v1/approvals`. (Approve is optional; with no
     Statuspage, approval publishes via `LoggingPublisher` — logged, not sent.)
  6. Record the observed failure mapping + outcome in the retro.

---

## Conventions checklist (held at quality review — standing)
- **Docstrings** on every new/changed module + public function citing the dossier §.
- **Named domain errors** — `GrailQueryError` (incl. FAILED state + poll timeout), `MalformedDqlRowError`
  (real required fields), `UnknownVendorStatusError`, `UnsupportedMonitorTypeError` (unmapped event.type).
- **Empty-input + precision-boundary tests** — empty `records` → `[]`; the ns-timestamp and ns-duration
  cases are the non-aligned-boundary tests (working agreement 2026-06-25).
- **Composition/assembly tests build REAL objects** — the run.py publisher-selection test must not patch
  the constructors whose wiring it asserts (2026-06-29 agreement; this is the story most exposed to it).
- **Frozen value types** — N/A new cross-field invariant; `LiveSecrets` optional fields are a field-bag.
- **Resource-lifecycle** — `run.py` engine dispose-on-every-exit-path unchanged; keep its test green.
- **Scoped staging; clean committed tree** — commit any `ruff format` reflow (2026-06-29 agreement).
- **Command-sync** — no new command this sprint (the run command exists); update CLAUDE.md only if a flag
  or env requirement changes (load_live_secrets now needs only the two Dynatrace vars — note it).
- **Wiki blast-radius** — at DoD, mechanical sweep over all `docs/scrum/wiki/*.md`; expected drift:
  `dynatrace-adapter` (query + executor + normalizer + health), `ingest-service-and-pull-loop` (run.py
  publisher selection), `statuspage-publish` (LoggingPublisher path), `config-layer`/`migrations-and-db`
  if settings.py changes. Update/re-verify every one the sweep reports.

## DoD gate (all six exit 0 on a CLEAN committed tree)
`pytest` · `lint-imports` (stays 5) · `python scripts/check_fk_direction.py` · `alembic upgrade head`
(no new migration) · `ruff check` · `ruff format --check`.

## Guardrails for the implementer
Build to THIS plan + the STORY-016b AC + the dossier + the saved real-schema reference — never to chat
history or the OLD illustrative field names. Do NOT write `.scrum/` board state. Do NOT run the reviewers
or merge. The async poll + the ns-timestamp parse are the two fiddly spots — test them with fakes
explicitly. Stop-and-report on a 3× overrun. The failure-status mapping (AC4) is intentionally finalized
during the live verification (T6) — do not invent failure values; map the known HEALTHY/0→UP and
fail-loud on the rest until the real value is observed.
