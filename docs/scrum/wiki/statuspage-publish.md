---
title: Statuspage publish adapter and best-effort publishing
code_refs: [backend/src/adapters/outbound/statuspage/__init__.py, backend/src/adapters/outbound/statuspage/status_mapping.py, backend/src/adapters/outbound/statuspage/http_executor.py, backend/src/composition/publish_helper.py, backend/src/composition/run.py, backend/tests/test_statuspage_adapter.py, backend/tests/test_statuspage_http_executor.py, backend/tests/test_publish_helper.py, backend/tests/fixtures/statuspage/component_operational.json, backend/tests/fixtures/statuspage/component_degraded.json]
verified_sha: d9c2a77
verified_sprint: sprint-20
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
- `publish_best_effort` wraps the publisher's `publish` call in a try/except (`backend/src/composition/publish_helper.py::publish_best_effort`).
- Catches any publish failure, logs it, and returns normally, ensuring Statuspage failures never roll back/crash the already-committed DB decision (`backend/src/composition/publish_helper.py::publish_best_effort`).
- `BestEffortPublisher` (`backend/src/composition/publish_helper.py::BestEffortPublisher`, STORY-016a) is a `StatusPublisherPort` that wraps a delegate publisher and routes every `publish` through `publish_best_effort`. `DecideService` calls `publisher.publish` directly and lets a failure PROPAGATE (its core contract), so the orchestration's `DecideService` is wired with this wrapper — a Statuspage outage on the recovery-publish path is logged + swallowed instead of crashing the pull cycle (AC3). The live composition root that injects it is now `composition/run.py::build_live_loop` (STORY-016): `DecideService(proposal_repo, publisher=BestEffortPublisher(RecordingPublisher(StatuspagePublisher)))` — see [[ingest-service-and-pull-loop]].
- `RecordingPublisher` (`backend/src/composition/publish_helper.py::RecordingPublisher`, STORY-037) is a `StatusPublisherPort` decorator that wraps a delegate publisher, a `PublicationRepository`, and a `ClockPort`. On each `publish`: (1) calls `delegate.publish(change)`; (2) IF the delegate succeeds, records a `Publication(component_id, status, published_at=clock.now())` via `publication_repo.record`. A raising delegate propagates BEFORE recording — nothing is written to the publications table (§12/T1.1: the table has no error column; record successes only). Composes inside `BestEffortPublisher`: `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))` — a publish failure is logged+swallowed and nothing recorded; a success is both published and recorded. The live chain is assembled in `composition/run.py::build_live_loop` (STORY-016), with `StatuspagePublisher`'s `component_mapping` supplied by `Config.statuspage_mapping()` (see [[config-layer]]).

### Testing and Fixtures
- No live Statuspage/HTTP connections. Testing uses recorded JSON fixtures under `backend/tests/fixtures/statuspage/`:
  - `component_operational.json`
  - `component_degraded.json`
- Tests inject a fake executor and verify the exact request parameters, headers, and payloads against these fixtures (`backend/tests/test_statuspage_adapter.py` ("Statuspage Adapter Tests")).
- `RecordingPublisher` is tested in `backend/tests/test_publish_helper.py` using only fakes (FakeClock, FakePublicationRepository, RecordingStatusPublisher, and a local RaisingPublisher). Four AC2 tests: record-on-success, nothing-on-failure (error propagates), BestEffortPublisher(RecordingPublisher(raising)) swallows+records-nothing, and published_at-uses-clock.now().
