---
id: STORY-030
title: Make dev_db.py up idempotent against a leftover container
type: chore
---

## Context
Follow-up from Sprint 8 retro. `scripts/dev_db.py up` fails with `docker: ... failed to bind host
port for 0.0.0.0:55432: address already in use` when a previous container named `uptime_pg_pytest`
is left behind (e.g. a prior run interrupted mid-start, leaving a stuck `Created` container that
still reserves the port). This hit the orchestrator ~twice in Sprint 8 and required a manual
`docker rm -f uptime_pg_pytest` before retrying. The helper should self-heal.

## Acceptance Criteria (refined — PO-approved 2026-06-26)
- [x] AC1: `dev_db.py up` removes any pre-existing container of its target name (`docker rm -f
      <name>`, ignoring "no such container") BEFORE attempting `docker run`, so a leftover/stuck
      same-named container no longer blocks startup.
- [x] AC2: `up` is idempotent: running `up` when a healthy container of that name is already running
      either reuses it or cleanly recreates it — no crash, and it ends with a migrated DB + the two
      printed URLs (current behavior on the happy path is preserved).
- [x] AC3: `down` still removes the container cleanly. A real port conflict from a DIFFERENT process
      (not our container) still surfaces a clear error (we only force-remove OUR named container, not
      whatever else might hold the port).
- [x] AC4: `lint-imports` + `pytest` stay green; if `dev_db.py` has unit-testable helpers, the new
      pre-clean step is covered; otherwise verify manually (start, leave a stuck container, `up`
      succeeds) and record the manual check.

## Resolved Questions
- Scope: only force-remove the helper's OWN container name; do not kill unrelated processes holding
  the port (AC3).

## History
- 2026-06-26: created from Sprint 8 retro (recurring leftover-container friction). Status: ready —
  bounded tooling fix, no open questions. Estimate: 1.
- 2026-06-27: verified idempotency using `test_up_idempotent_against_leftover_container` integration test in `backend/tests/test_dev_db_cli.py`. The test starts a container, runs the CLI `up` command, asserts it cleans and starts successfully, then tears it down via `down`. All tests pass.

