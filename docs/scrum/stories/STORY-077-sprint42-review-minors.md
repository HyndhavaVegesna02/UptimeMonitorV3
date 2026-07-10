---
id: STORY-077
title: Chore — sprint-42 review minors (zone-layout meta-test private-API coupling; decisions concurrency comment)
type: chore
---

## Context
Two NON-blocking MINOR findings from the Sprint 42 Opus reviews (STORY-074/075). Neither blocked
acceptance; grouped here for a cleanup pass.

## Description / checklist
- **MINOR-1 (from STORY-074 quality review):** `backend/tests/test_zone_layout.py` asserts router
  inclusion by importing FastAPI's PRIVATE `_IncludedRouter` and reading `.original_router`. This
  works on the installed FastAPI 0.138.0 and is fail-loud (a rename errors the import, not a silent
  pass), but it couples the meta-test to a FastAPI internal. Replace the check with a public-API
  assertion (e.g. inspect `app.routes` / route path prefixes, or the aggregated router's public
  structure) OR, if no clean public equivalent exists, pin the FastAPI lower bound in
  `pyproject.toml` and add a comment flagging the private-API dependency.
- **MINOR-2 (from STORY-075 quality review):** the strip in STORY-075 removed a useful
  concurrency-nuance comment from `backend/src/api/v1/decisions/service.py` explaining that
  `ProposalNotOpenError → 409` covers BOTH the up-front open-state guard AND a lost-race resolve
  (concurrent double-submit surfaced by the repository, per the 2026-06-28 TOCTOU agreement).
  Restore it as a comment beside the decisions flow (or in `ApprovalService`) so the subtlety
  isn't lost — `_shared/errors.py` is now a bare mapping and carries no such context.

## Acceptance Criteria
- [ ] `test_zone_layout.py` no longer imports a FastAPI private symbol (or the FastAPI floor is
      pinned with a comment); the test still fails on all three drift directions (feature missing
      from the contract list; feature missing from the aggregator; extra unregistered feature dir).
- [ ] The decisions concurrency nuance is documented in code again (comment beside the relevant
      flow), citing the lost-race/TOCTOU behavior.
- [ ] Backend six-gate DoD green; wiki blast radius resolved via the mechanical sweep.

## Open Questions
None.

## References
- Sprint 42 review: `docs/scrum/sprints/2026-07-10-sprint-42/review.md` (non-blocking items).
- Related: STORY-074, STORY-075; the 2026-06-28 TOCTOU/check-then-act working agreement.

## History
- 2026-07-10: filed from Sprint 42 review MINORs (PO accepted 074/075/076 + requested this follow-up). Status: draft (needs estimate at refinement).
