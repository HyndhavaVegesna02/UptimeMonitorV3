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
Make a `native_id` that contains a quote (or other query-breaking character) fail safely
rather than malform the DQL silently — either by validating + rejecting it with a clear
error, or by escaping it. Decide the approach at refinement.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Given a `native_id` containing a `"` (or other DQL-breaking character),
      `build_dql_query` does NOT emit a silently-malformed query — it either raises a clear
      error or safely escapes the value (approach chosen at refinement).
- [ ] AC2: A test covers the quote-containing `native_id` case; existing query-builder
      tests still pass; `lint-imports` stays green.

## Open Questions
- Reject (validate + clear error) vs escape (sanitize into the query)? Decide at refinement
  — reject is simpler and matches "trusted config, surface a misconfig loudly"; escape is
  more permissive. This open question keeps the story `draft` until resolved.

## History
- 2026-06-25: created from Sprint 4 review (PO asked both STORY-008 minors become chores).
  Status: draft — has an open question (reject vs escape) to resolve at refinement.
  Proposed estimate: 1.
