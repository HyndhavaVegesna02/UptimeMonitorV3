---
id: STORY-073
title: Defect — dev_db container-lifecycle tests flake under full-suite Docker contention
type: defect
---

## Context
Found at sprint-41 STORY-070 DoD gate (2026-07-09). Under a single canonical `pytest`
invocation, the self-container-spawning DB-lifecycle tests intermittently fail:
- `backend/tests/test_dev_db_cli.py` (`test_up_then_check_fk_direction_then_down`,
  `test_up_idempotent_against_leftover_container`)
- `backend/tests/test_dev_db_fixture.py` (`test_spawn_failure_does_not_leak_a_container`,
  `test_container_is_torn_down_even_when_a_test_using_the_fixture_fails`)

Across three full-suite runs a DIFFERENT subset failed each time (2 failed / 1 failed /
1-different failed), always with a Docker-timing symptom: `docker exec … pg_isready`
timing out (`scripts/dev_db.py:134` `wait_for_postgres` `TimeoutError`) or the
alembic-in-subprocess step failing (`dev_db.py:163` `RuntimeError`). These tests each spin
up their OWN throwaway `postgres:16` container (on ephemeral ports) while the rest of the
suite hammers the shared `migrated_db` DB on 55432, and the extra containers terminate
abnormally / fail readiness under the concurrent Docker load.

This is the same CLASS of flaky-gate as the fixed STORY-054 (CheckHistoryPage) and the
in-flight STORY-068 (useAvailability) — but backend, and rooted in Docker container churn
rather than Vitest CPU contention. The 2026-07-06 working agreement says a flaky gate is
never left standing.

## Contention proof (per the 2026-07-06 agreement — this is contention, not a real red)
- **Empty diff since the sprint cut:** `git diff sprint-41-start..HEAD -- backend/tests/test_dev_db_cli.py backend/tests/test_dev_db_fixture.py scripts/dev_db.py` is empty — untouched by STORY-070.
- **Green in single-file isolation:** `test_dev_db_cli.py` alone = 2/2 in ~15s (twice);
  `test_dev_db_fixture.py` alone = 6/6 in ~9s (warm Docker). The full suite excluding both files = 523 passed.
So every test passes; they simply cannot share one Docker host concurrently with the big
parallel DB suite. STORY-070's own code was never at fault.

## Description (to refine)
Make the canonical `pytest` deterministic when the container-lifecycle tests run alongside
the rest of the suite. Candidate approaches (refine/choose at planning):
- Serialize / xdist-group the container-spawning lifecycle tests so no two run concurrently
  (and not concurrently with heavy DB-gated tests).
- Gate them behind a marker (e.g. `@pytest.mark.docker_lifecycle`) with a longer, tunable
  `READY_TIMEOUT_SECONDS`, run in their own step.
- Reuse the session container instead of spawning fresh ones where the test's intent allows.

## Acceptance Criteria (to refine)
- [ ] Root cause characterized (readiness timeout vs container-start failure under load).
- [ ] Canonical `pytest` passes deterministically across repeated runs, including the
      container-lifecycle tests, on a warm Docker host.
- [ ] No loss of the lifecycle behaviors these tests protect (teardown-on-failure, idempotent
      up, no leaked container) — they still assert the same guarantees.

## Decided (sprint-43 planning, PO 2026-07-10)
- **Mechanism = robust, tunable readiness (not marker-gating the tests out of the canonical
  gate).** The lifecycle tests MUST keep running inside the canonical `pytest` (marker-gating them
  into a separate step would weaken the single-command DoD floor). Make container readiness survive
  a loaded Docker host: in `scripts/dev_db.py::wait_for_postgres`, raise the default readiness
  budget and add a patient retry/backoff loop (each `docker exec … pg_isready` attempt bounded, the
  overall wait tunable via an env var / module constant, e.g. `DEV_DB_READY_TIMEOUT_SECONDS`), so a
  slow-to-ready container under concurrent Docker load is waited-out rather than failing. If a
  container genuinely fails to start (not just slow), still raise cleanly and tear down (preserve the
  teardown-on-failure guarantee — 2026-06-25 agreement).
- If robust readiness alone does not make it deterministic, the sanctioned fallback is to SERIALIZE
  the container-spawning lifecycle tests relative to each other (a shared file lock / ordering), NOT
  to remove them from the gate. Container-reuse is rejected (the tests' whole intent is to exercise
  the real spawn/teardown lifecycle).

## Acceptance Criteria (refined, sprint-43)
- [x] Root cause characterized in the story/PR (readiness timeout under load vs container-start
      failure), with evidence.
- [x] The canonical `pytest` (single invocation, warm Docker host, NO `--ignore`) passes
      deterministically INCLUDING `test_dev_db_cli.py` + `test_dev_db_fixture.py` — demonstrated by
      repeated full-suite runs (≥3) all green. (This retires the "resource-isolated valid signal"
      workaround used in sprints 41–42.)
- [x] The lifecycle guarantees are UNCHANGED: teardown-on-failure, idempotent `up` against a
      leftover container, no leaked container on partial-setup failure — the same assertions still
      hold (tests not weakened/skipped).
- [x] If `scripts/dev_db.py` gains a tunable timeout knob or any command/behavior change, CLAUDE.md
      is updated in the same commit (command-sync agreement 2026-06-23).
- [x] Backend six-gate DoD green; wiki blast radius resolved via the mechanical sweep (expect
      `dev-setup-and-dod` — `scripts/dev_db.py` is in its `code_refs`).

## Open Questions
None — mechanism decided above (robust readiness; serialize as fallback; no marker-gating, no reuse).

## History
- 2026-07-09: filed from sprint-41 STORY-070 DoD gate. Status: draft (needs refinement + estimate).
- 2026-07-10: refined at sprint-43 planning; mechanism = robust tunable readiness (keep the tests in
  the canonical gate). Estimate 3 pts. Status: ready.
- 2026-07-10: Resolved via implementation of robust container readiness checks in scripts/dev_db.py. Bounded each docker exec pg_isready attempt to 5.0s and introduced a retry/backoff sleep loop (up to 5.0s max sleep per iteration) with a raised budget (60s default, overridable via DEV_DB_READY_TIMEOUT_SECONDS). Teardown-on-failure is preserved. Checked in 3 green full-suite runs on a warm host. Wiki updated for dev-setup-and-dod.md. Final SHA: 335a71e (code) and 335a71e (wiki).
  Green run log outputs:
  * Run 1: 548 passed in 89.05s (task-94)
  * Run 2: 548 passed in 81.10s (task-98)
  * Run 3: 548 passed in 91.96s (task-102)
