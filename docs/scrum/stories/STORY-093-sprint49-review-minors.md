---
id: STORY-093
title: Chore — sprint-49 review minors (container hardening, health grace, test hygiene)
type: chore
---

## Context
Follow-up from the sprint-49 review (PO accepted 087/092/088 with these non-blocking minors
captured here per accept-with-follow-up). None block; all surfaced by the spec/quality reviews.

## Description
Apply the deferred sprint-49 review minors across the container image, the CloudFormation
template, and a couple of test-hygiene spots.

## Acceptance Criteria
- [ ] AC1 (container hardening): the `Dockerfile` runs as a non-root `USER`; the dead
      `ENV PORT=8000` is removed (the CMD hard-codes `--port 8000`); dependency install is
      ordered so a source-only change does not invalidate the `pip install` layer (copy
      `pyproject.toml` + install deps before copying `backend/`, or equivalent).
- [ ] AC2 (ECS health grace): `infra/stack.yaml` `APIService` sets a
      `HealthCheckGracePeriodSeconds` sufficient for the first-boot lifespan seed so a slow
      boot does not churn the task; `cfn-lint infra/stack.yaml` stays green.
- [ ] AC3 (test hygiene): `backend/tests/test_run_live_loop.py::test_main_resource_lifecycle_success`
      makes a real assertion (e.g. `seed_topology_dynamo` / `build_live_loop` invoked) or is
      removed; add the plan step-4 guard test asserting no `sqlalchemy`/`create_engine`/`psycopg`
      under `backend/src`; replace the raw `os.environ` try/finally in
      `test_topology_endpoint.py` with `monkeypatch.setenv`.
- [ ] AC4 (gates): full amended DoD gate green (pytest incl. DynamoDB-Local, import-linter,
      ruff check/format, cfn-lint) + frontend.

## Open Questions
None.

## History
- 2026-07-16: filed at sprint-49 review from the spec/quality review minors; PO accepted the
  three sprint-49 stories with these captured as a follow-up chore. Refine/estimate at next
  planning.
