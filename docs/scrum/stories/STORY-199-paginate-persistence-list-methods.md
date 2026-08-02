---
id: STORY-199
title: Paginate the five adapters/persistence/ methods (across four files) that silently truncate against an "all" port contract
type: defect
points: 3
status: ready
refined: 2026-07-31
re_refined: 2026-08-02
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
- [ ] **AC5** — `_EXEMPTIONS` in `backend/tests/test_zr7_pagination_guard.py:71` is **EMPTY** at the
      end of this story, and both ZR-7 tests pass. All five current entries name this story as their
      fix (`"Fix: STORY-199."`), so landing the fix without removing them is itself a failure — the
      guard's second test asserts that every exemption still corresponds to a real unpaginated call
      site, and will go RED on a stale entry. **Do not re-key the entries to the new line numbers;
      remove them.** This AC is self-verifying and is the cheapest evidence in the story: the guard
      written in sprint 66 was designed to detect exactly this story landing.
- [ ] **AC6** — Mutation proof (standing evidence rule): with all five fixed, remove the
      `LastEvaluatedKey` loop from ONE method, confirm that method's AC2 test goes RED **and** that
      the ZR-7 guard goes RED naming that call site, then restore and confirm `git diff` is empty.
      A fix whose removal turns nothing red is unpinned.

## Notes for the implementer

**`is_under_maintenance` is not a "collect everything" loop, and must not become one.** It answers a
boolean. The correct shape is: page until a match is found, return `True` immediately on the first
matching item, and return `False` only after `LastEvaluatedKey` is exhausted. Accumulating every
page into a list before testing would be correct but needlessly reads the whole GSI partition on the
common "not under maintenance" path — and that path runs every cycle in `decide`.

**Why AC2's test must force the page boundary.** The defect only appears past a 1 MB page. A test
over a handful of rows passes while the defect stands, which is why the audit's own CLEAN verdict on
this file was wrong. The `_limit` hook is what makes the boundary reachable without a megabyte of
fixtures.

## Open Questions

None.

## History

- 2026-07-31: filed from STORY-195's quality-review fix round finding (`ZR-7`,
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2c/§6).
- 2026-08-02: refined to `ready` at sprint-67 planning. Every citation in this file was
  re-derived against HEAD (`86459ea`) and **all of them still hold** — `is_under_maintenance` def
  at :86 / query at :90, `list_windows` :66/:68, `list_components` :28/:29, `list_signals` :29/:30,
  `list_open` :172/:174, the reference loop at `dynamo_observation_repository.py` :93-118 with the
  `_limit` hook at :23. Added **AC5** (empty the ZR-7 exemption list) and **AC6** (mutation proof),
  neither of which could have been in the original file: the ZR-7 guard did not exist when it was
  written — STORY-197 landed it later the same day, with five exemptions that all name this story.
