---
title: Statuspage publish adapter and best-effort publishing
code_refs: [backend/src/adapters/outbound/statuspage/, backend/src/composition/publish_helper.py, backend/tests/test_statuspage_adapter.py]
verified_sha: b4d5414
verified_sprint: sprint-9
status: verified
---

## Facts (verified against code)

### Statuspage Outbound Adapter (`adapters/outbound/statuspage/`, Zone 5)
- `StatuspagePublisher` implements the core's `StatusPublisherPort` interface to push status changes to Statuspage (`__init__.py:18`).
- An injected `Executor` seam handles the HTTP calls (`__init__.py:13`, `publish` method `:33`).
- Resolves `component_id` -> Statuspage component ID via an injected `component_mapping: dict[str, str]` passed to constructor (`__init__.py:20`).
- If `component_id` is not present in the mapping, `UnmappedComponentIdError` is raised (`__init__.py:36`).
- Maps `ComponentStatus` to Statuspage status string via `map_component_status` (`status_mapping.py:16`). Exhaustive mapping over canonical enums: operational, degraded_performance, partial_outage, major_outage. Raises `UnknownComponentStatusError` on unknown status.
- Translates `publish` call to a `PATCH` request to: `https://api.statuspage.io/v1/pages/{page_id}/components/{vendor_component_id}` with OAuth header and JSON payload (`__init__.py:41`).

### Composition Best-effort helper (`composition/publish_helper.py`, Zone 5)
- `publish_best_effort` wraps the publisher's `publish` call in a try/except (`publish_helper.py:8`).
- Catches any publish failure, logs it, and returns normally, ensuring Statuspage failures never roll back/crash the already-committed DB decision (`publish_helper.py:19`).

### Testing and Fixtures
- No live Statuspage/HTTP connections. Testing uses recorded JSON fixtures under `backend/tests/fixtures/statuspage/`:
  - `component_operational.json`
  - `component_degraded.json`
- Tests inject a fake executor and verify the exact request parameters, headers, and payloads against these fixtures (`test_statuspage_adapter.py:44`).
