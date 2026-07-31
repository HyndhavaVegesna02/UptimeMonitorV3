---
id: STORY-199
title: Paginate the five adapters/persistence/ methods (across four files) that silently truncate against an "all" port contract
type: defect
points: 3
status: draft
refined: 2026-07-31
---

## Context

Filed from the sprint-66 audit's quality-review fix round (STORY-195,
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2c). An independent re-audit of
STORY-195's own footprint found a real, previously-unreported production defect: several
`adapters/persistence/` methods pair an unbounded DynamoDB `query` with a post-read filter and no
`LastEvaluatedKey` loop, against port contracts (`core/ports/*`) whose docstrings promise a complete
result set. This is now catalogued as `ZR-7` in `docs/scrum/wiki/zone-rules.md`.

## Description

`backend/src/adapters/persistence/dynamo_maintenance_repository.py:86-97`
(`is_under_maintenance`) issues an UNBOUNDED `query` (`gsi1pk="MAINT" AND gsi1sk <= <now>#�` —
every maintenance window ever created, for every component, with no `Limit`), applies a POST-READ
`FilterExpression` narrowing to `component_id`/`ends_at > at`, and discards `LastEvaluatedKey` — it
never loops. DynamoDB applies `FilterExpression` AFTER the 1 MB per-page read limit, so once total
maintenance-window volume exceeds one page, a component that IS under maintenance can silently receive
`False` from this method — a wrong answer, not an error — which `core/services/decide.py`'s
suppression logic then silently fails to apply.

Four siblings share the identical shape, against port contracts that explicitly promise completeness:

- `backend/src/adapters/persistence/dynamo_maintenance_repository.py:66-84` (`list_windows`) — port
  promise "Retrieve all scheduled maintenance windows"
  (`backend/src/core/ports/maintenance_repository.py:13-19`).
- `backend/src/adapters/persistence/dynamo_component_repository.py:28-34` (`list_components`) — port
  promise "Retrieve all components from the spine"
  (`backend/src/core/ports/component_repository.py:18-25`).
- `backend/src/adapters/persistence/dynamo_signal_repository.py:29-36` (`list_signals`) — port promise
  "Retrieve every seeded signal" (`backend/src/core/ports/signal_repository.py:18-25`).
- `backend/src/adapters/persistence/dynamo_proposal_repository.py:172-179` (`list_open`) — port
  promise "Retrieve all OPEN status proposals... A list of all open proposals"
  (`backend/src/core/ports/proposal_repository.py:57-64`).

The correct pattern already exists in the SAME directory:
`backend/src/adapters/persistence/dynamo_observation_repository.py:100-118` (`in_window`'s
`while True` / `ExclusiveStartKey` / `LastEvaluatedKey` loop), with a test-only pagination hook
(`self._limit: int | None = None  # Hook for testing pagination`,
`backend/src/adapters/persistence/dynamo_observation_repository.py:23`) that lets a test force a small
page size without needing a real 1 MB of data. This is not a missing capability — it is an
inconsistently-applied one.

**Not in scope:** `backend/src/adapters/persistence/dynamo_publication_repository.py::list_recent`
uses `Limit=limit` (default 50), and its own port docstring promises only "up to `limit`
most-recent" — a stated bound, not an "all"/"every" contract. Honoring a stated limit is compliant,
not a violation, and is excluded from this story.

## Acceptance Criteria

- [ ] **AC1** — Each of the five call sites (`is_under_maintenance`, `list_windows`,
      `list_components`, `list_signals`, `list_open`) loops on `LastEvaluatedKey` exactly as
      `dynamo_observation_repository.py::in_window` already does, rather than reading a single page.
- [ ] **AC2** — Each of the four files (five methods: dynamo_maintenance_repository.py owns TWO —
      `is_under_maintenance` and `list_windows`) gains a test-only page-size hook (mirroring `_limit` at
      `dynamo_observation_repository.py:23`), and a test that sets it small, seeds MORE rows than one
      page, and asserts the method still returns/checks the COMPLETE set. This test is demonstrated
      FAILING against the pre-fix code (per the project's mutation/pre-fix-demonstration standing
      rule) before the fix lands, then passing after — with the failing run recorded on the board.
- [ ] **AC3** — `is_under_maintenance` specifically gets a test proving a component whose ONLY
      matching window is on a page past the hook's forced small page size still returns `True` — the
      exact silent-`False` shape this finding describes, not just "list has more than N items."
- [ ] **AC4** — Existing contract tests for all five methods continue to pass unchanged for the
      single-page case.

## Open Questions

None.

## History

- 2026-07-31: filed from STORY-195's quality-review fix round finding (`ZR-7`,
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2c/§6).
