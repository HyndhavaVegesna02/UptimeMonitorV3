---
title: Statuspage publish adapter and best-effort publishing
code_refs: [backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/outbound/statuspage/status_mapping.py, backend/src/adapters/outbound/statuspage/http_executor.py, backend/src/composition/publish_helper.py, backend/src/composition/run.py, backend/tests/test_statuspage_adapter.py, backend/tests/test_statuspage_http_executor.py, backend/tests/test_publish_helper.py, backend/tests/fixtures/statuspage/component_operational.json, backend/tests/fixtures/statuspage/component_degraded.json]
verified_sha: d441468
verified_sprint: sprint-36
status: verified
---

## Facts (verified against code)

### Statuspage Outbound Adapter (`adapters/outbound/statuspage/`, Zone 5)
- `StatuspagePublisher` implements the core's `StatusPublisherPort` interface to push status changes to Statuspage (`backend/src/adapters/outbound/statuspage/__init__.py::StatuspagePublisher`).
- An injected `Executor` seam handles the HTTP calls (`backend/src/adapters/outbound/statuspage/__init__.py::Executor`, and `publish` method `backend/src/adapters/outbound/statuspage/__init__.py::StatuspagePublisher.publish`).
- Resolves `component_id` -> Statuspage component ID via an injected `component_mapping: dict[str, str]` passed to constructor (`backend/src/adapters/outbound/statuspage/__init__.py::StatuspagePublisher.__init__`).
- If `component_id` is not present in the mapping, `UnmappedComponentIdError` is raised (`backend/src/adapters/outbound/statuspage/__init__.py::UnmappedComponentIdError`).
- Maps `ComponentStatus` to Statuspage status string via `map_component_status` (`backend/src/adapters/outbound/statuspage/status_mapping.py::map_component_status`). Exhaustive mapping over canonical enums: operational, degraded_performance, partial_outage, major_outage. Raises `UnknownComponentStatusError` on unknown status.
- Translates `publish` call to a `PATCH` request to: `https://api.statuspage.io/v1/pages/{page_id}/components/{vendor_component_id}` with OAuth header and JSON payload (`backend/src/adapters/outbound/statuspage/__init__.py::StatuspagePublisher.publish`).

### Real HTTP Executor (`statuspage/http_executor.py`, STORY-016)
- `make_statuspage_executor(*, http_request=httpx.request) -> Executor`
  (`backend/src/adapters/outbound/statuspage/http_executor.py::make_statuspage_executor`) returns the
  real `Executor` closure: calls `http_request(method, url, headers=, json=)`, returns the parsed JSON
  (`{}` on an empty body), and raises the named `StatuspageApiError` (a `RuntimeError`,
  `http_executor.py::StatuspageApiError`) on a non-2xx response — so the surrounding
  `BestEffortPublisher` swallows a failed publish on the recovery path. The `http_request` seam
  (default `httpx.request`) keeps it unit-testable with no live call; it never leaks `httpx.Response`
  across the boundary (returns a plain `dict`). Tested in `backend/tests/test_statuspage_http_executor.py`.

### Composition Best-effort helper (`composition/publish_helper.py`, Zone 5)
- `BestEffortPublisher` (`backend/src/composition/publish_helper.py::BestEffortPublisher`, STORY-016a) is a `StatusPublisherPort` that wraps a delegate publisher. Its `publish` method wraps `self._delegate.publish(change)` in a try/except DIRECTLY (STORY-047 AC2, sprint-36: the pre-existing standalone `publish_best_effort` free function was folded into this method — the one canonical best-effort seam — rather than the two coexisting). Catches any publish failure, logs it, and returns normally, ensuring Statuspage failures never roll back/crash the already-committed DB decision. `DecideService` calls `publisher.publish` directly and lets a failure PROPAGATE (its core contract), so the orchestration's `DecideService` is wired with this wrapper — a Statuspage outage on the recovery-publish path is logged + swallowed instead of crashing the pull cycle (AC3). As of STORY-045, this sits INSIDE `StatusWritebackPublisher` in the shared chain (see below) — see [[ingest-service-and-pull-loop]]. `backend/tests/test_statuspage_adapter.py::test_best_effort_publisher_catches_and_logs_error` (renamed from `test_publish_best_effort_catches_and_logs_error`) now exercises the try/except through `BestEffortPublisher` directly, since the free function it used to call no longer exists.
- `RecordingPublisher` (`backend/src/composition/publish_helper.py::RecordingPublisher`, STORY-037) is a `StatusPublisherPort` decorator that wraps a delegate publisher, a `PublicationRepository`, and a `ClockPort`. On each `publish`: (1) calls `delegate.publish(change)`; (2) IF the delegate succeeds, records a `Publication(component_id, status, published_at=clock.now())` via `publication_repo.record`. A raising delegate propagates BEFORE recording — nothing is written to the publications table (§12/T1.1: the table has no error column; record successes only). Composes inside `BestEffortPublisher`: `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))` — a publish failure is logged+swallowed and nothing recorded; a success is both published and recorded. `StatuspagePublisher`'s `component_mapping` is supplied by `Config.statuspage_mapping()` (see [[config-layer]]).
- `LoggingPublisher` (`backend/src/composition/publish_helper.py::LoggingPublisher`, STORY-016b) is a no-op `StatusPublisherPort` that logs the change and does nothing. Used (as the delegate wrapped by `StatusWritebackPublisher`) when Statuspage is NOT configured — i.e. the Statuspage secrets or the config mapping are absent — so the live loop runs **Dynatrace-only** for the internal verification (STORY-016b: "verify internally; external is bound to work"). It wraps no `RecordingPublisher`, so nothing is written to the publications table on the no-op path.
- `StatusWritebackPublisher` (`backend/src/composition/publish_helper.py::StatusWritebackPublisher`, STORY-045, dossier §9/§12/§14 T1.1) is a `StatusPublisherPort` decorator wrapping a delegate publisher AND a `ComponentRepository`. On `publish`: (1) `component_repo.set_status(change.component_id, change.status)` FIRST — a durable DB write; (2) THEN `delegate.publish(change)`. Sits OUTSIDE `BestEffortPublisher` (the write-back must PROPAGATE on failure — e.g. `ComponentNotFoundError` on an unknown component id — while only the external Statuspage call inside the delegate chain is best-effort). Because the write-back happens before the delegate is invoked, a delegate failure (swallowed further in by `BestEffortPublisher`) can never undo it. This is the fix for STORY-045's headline defect: before this story, `components.status` was never written after seeding, so the Dashboard was frozen and `decide`'s recovery branch was unreachable.
- `build_publisher` (`backend/src/composition/publish_helper.py::build_publisher`, STORY-045, D2) is the ONE shared assembly both composition roots use — `composition/run.py::build_live_loop` (the recovery trigger) AND `composition/app.py::create_app` (the approve trigger, see [[api-five-file-convention]]) — so the two chains can never drift (2026-06-25 share-the-assembly agreement):
  - Statuspage page id, api token, AND a non-empty `component_mapping` all present: `StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(StatuspagePublisher(...))), component_repo)`.
  - Otherwise: `StatusWritebackPublisher(LoggingPublisher(), component_repo)` — the write-back still applies on the no-creds local dev path (memory: local dev exists to SEE live results).
  `composition/run.py::build_live_loop` now calls `build_publisher` instead of assembling the chain inline (its previous `StatuspagePublisher`/`make_statuspage_executor` imports moved into `build_publisher`).

### Testing and Fixtures
- No live Statuspage/HTTP connections. Testing uses recorded JSON fixtures under `backend/tests/fixtures/statuspage/`:
  - `component_operational.json`
  - `component_degraded.json`
- Tests inject a fake executor and verify the exact request parameters, headers, and payloads against these fixtures (`backend/tests/test_statuspage_adapter.py` ("Statuspage Adapter Tests")).
- `RecordingPublisher` is tested in `backend/tests/test_publish_helper.py` using only fakes (FakeClock, FakePublicationRepository, RecordingStatusPublisher, and a local RaisingPublisher). Four AC2 tests: record-on-success, nothing-on-failure (error propagates), BestEffortPublisher(RecordingPublisher(raising)) swallows+records-nothing, and published_at-uses-clock.now().
- `StatusWritebackPublisher` + `build_publisher` are tested in `backend/tests/test_publish_helper.py` (STORY-045): write-before-delegate ordering (a spy delegate reads the fake repo's status when called), survives a `BestEffortPublisher`-swallowed delegate failure (write-back stands, nothing recorded), an unknown component id propagates `ComponentNotFoundError` before the delegate is ever reached, and `build_publisher` assembles both D2 shapes (creds+mapping present vs absent, including the empty-mapping-with-creds edge). `backend/tests/test_run_live_loop.py::test_build_live_loop_assembly` (rewritten, not deleted, per the 2026-06-29 contract-change agreement) now asserts the real chain nests `StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(StatuspagePublisher)))` under `DecideService._publisher`.

## History
- sprint-36 (STORY-047, quality-review minors chore): AC2 folded the standalone
  `publish_best_effort` free function into `BestEffortPublisher.publish` directly (Fact
  updated above) — one canonical best-effort seam instead of two coexisting. No behavior
  change; `composition/__init__.py`'s re-export of the free function was removed (see
  [[architecture-boundary]]). `backend/tests/test_statuspage_adapter.py`'s coverage of the
  try/except was rewritten to go through `BestEffortPublisher` (renamed test, same
  assertions). verified_sha → d441468.
- sprint-29 (STORY-045): added `StatusWritebackPublisher` and the shared `build_publisher` assembly (D1/D2); refactored `composition/run.py::build_live_loop` to consume `build_publisher` instead of its previous inline chain — `DecideService._publisher` now nests a `StatusWritebackPublisher` outermost, so `test_run_live_loop.py`'s two assembly tests were rewritten (not deleted) to assert the new nesting. `composition/app.py::create_app` (see [[api-five-file-convention]]) is the second composition root now consuming `build_publisher`. verified_sha → 7cabee7.
- sprint-31 (STORY-048, a TEMPORARY feature — see [[sample-mode]]): the publisher chain itself is
  UNCHANGED. `composition/run.py` was touched only by an UNRELATED seam one step earlier in
  `build_live_loop` — its step 2 (`ingest_port`, BEFORE the publisher assembly this article
  describes) now wraps the real `IngestService` in a `SampleModeIngest` decorator (the on-demand
  outage simulator); step 4 (`build_publisher`) and everything downstream of it is byte-identical.
  Re-verified; no Fact in this article changed. verified_sha → 0ea652e.
- sprint-36 (STORY-043, mechanical staleness sweep only): the publisher chain itself is UNCHANGED.
  `composition/run.py` gained ONE unrelated line before ANY of this article's code runs — a
  `load_dotenv()` call at the very top of `main()`, before `load_settings`/`load_live_secrets`
  (see [[dev-setup-and-dod]] and [[ingest-service-and-pull-loop]]) — `build_live_loop` and
  `build_publisher` themselves are byte-identical. Re-verified; no Fact in this article changed.
  verified_sha → 6a33edb.
