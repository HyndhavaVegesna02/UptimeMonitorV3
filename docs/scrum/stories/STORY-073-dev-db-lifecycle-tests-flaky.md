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

## Open Questions
- Serialize vs marker-gate vs container-reuse — which best preserves the tests' intent?

## History
- 2026-07-09: filed from sprint-41 STORY-070 DoD gate. Status: draft (needs refinement + estimate).
