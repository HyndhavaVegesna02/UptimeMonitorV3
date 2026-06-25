---
id: STORY-021
title: Guard native_id interpolation in the DQL query builder
type: chore
---

## Context
Follow-up from Sprint 4 review (STORY-008 quality-review minor, non-blocking). In
`backend/src/adapters/inbound/dynatrace/query.py:48-54`, `build_dql_query` interpolates
`native_id` into the DQL filter string unescaped. It is documented in-code as trusted
vendor config (the monitor id we configured in Dynatrace, not end-user input) on a
read-only Grail fetch, so there is no injection vector today — but a `native_id`
containing a `"` would silently malform the query. This chore closes the latent foot-gun.

## Description
Make a `native_id` that contains a query-breaking character (e.g. a double-quote) fail
safely rather than malform the DQL silently. **Approach (PO-approved 2026-06-25): REJECT
with a clear error** — validate `native_id` in `build_dql_query` and raise a clear error
on a query-breaking character, matching "trusted config: surface a misconfiguration loudly"
(no silent escaping/sanitizing).

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [x] AC1: Given a `native_id` containing a `"` (or other DQL-breaking character),
      `build_dql_query` raises a clear, named error — it never emits a silently-malformed
      query.
- [x] AC2: A well-formed `native_id` still builds the same query as today (no regression);
      a test covers both the rejecting case and the unchanged happy path.
- [x] AC3: `lint-imports` stays green; the existing STORY-008 query-builder tests still pass
      unchanged.

## Resolved Questions
- Reject vs escape: **REJECT with a clear error** (PO-approved at refinement, 2026-06-25).

## History
- 2026-06-25: created from Sprint 4 review (PO asked both STORY-008 minors become chores).
- 2026-06-25: refined. Open question resolved (reject, not escape); AC1–AC3 finalized;
  estimate 1. Status: ready — for Sprint 6 (Sprint 5 commits STORY-009 + STORY-020 = 6 pts).
- 2026-06-25: implemented. Added `InvalidNativeIdError` (named `ValueError` subclass) and a
  guard in `build_dql_query` rejecting `native_id` values containing `"`, backslash, or a
  newline. Two tests added: rejecting case (`native_id='a"b'`) and a no-regression check that
  a well-formed `native_id` builds the exact same query string as before. All four DoD gates
  green; `lint-imports` 3 kept/0 broken. `docs/scrum/wiki/dynatrace-adapter.md` re-verified and
  `verified_sha` bumped to ae5f880.
