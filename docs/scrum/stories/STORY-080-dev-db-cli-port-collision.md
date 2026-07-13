---
id: STORY-080
title: dev_db CLI tests — remove the hardcoded 55433 port collision
type: defect
---

## Context
Filed from sprint 44 (STORY-079's gate self-run, 2026-07-12), per the 2026-07-06 agreement that
a contention-capable gate is never left standing. `backend/tests/test_dev_db_cli.py::
test_up_then_check_fk_direction_then_down` and `test_up_idempotent_against_leftover_container`
hardcode host port 55433 for the throwaway container they spawn — any externally running
container on that port (e.g. a second reviewer/demo DB, exactly what sprint 44 ran) false-reds
them. Proven contention in-sprint: empty product diff + both tests pass in isolation (2 passed,
15.19s) with the external container stopped.

## Description
Make the two CLI-path tests port-collision-proof: pick a free scratch port at test time (or
honor an env override), so no external container can false-red the canonical `pytest` gate.

## Acceptance Criteria
- [ ] AC1: the dev_db CLI tests no longer bind a fixed host port — a container already bound to
      55433 (or any chosen port) does not affect them; regression test/pattern proves it.
- [ ] AC2: canonical `pytest` green with an unrelated Postgres container running on 55433.
- [ ] Six-gate DoD green; wiki blast radius resolved (sweep decides).

## Open Questions
<!-- none -->

## History
- 2026-07-12: filed from sprint-44 STORY-079 gate contention (proof recorded in the story report).
