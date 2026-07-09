---
id: STORY-075
title: api/v1/_shared foundation — central domain-exception→HTTP registry replacing per-feature mapping
type: chore
---

## Context
From the 2026-07-10 API restructure proposal (§3.4 G2/G5, §6.2, §10 Phase 2). Exception→HTTP
mapping is inconsistent and partially duplicated today: `availability/controller.py` maps
`SignalIntervalUnconfiguredError→409` twice (and 422 twice) within one file; `history/controller.py`
maps in the controller; `decisions/service.py` and `maintenance/service.py` map in the *service*
layer instead; six features map nothing. STORY-017 (CORS/auth) also has no api-side landing zone.
This story creates the api zone's owned shared-edge package and centralizes error semantics —
giving the zone the weight it rightfully owns (HTTP policy) without moving any domain logic.

## Description
Create `backend/src/api/v1/_shared/` (underscore = not a feature; excluded from
`api-feature-independence`) with `errors.py`: one registry mapping domain exceptions to HTTP
statuses, installed as FastAPI exception handlers via `install_error_handlers(app)`. Strip the
per-feature mapping (availability + history controllers; decisions + maintenance services). Add
an empty `middleware.py` seam (module + docstring only — STORY-017 lands there later; no logic
now). Fence `_shared` with its own contract.

## Acceptance Criteria
- [x] `backend/src/api/v1/_shared/errors.py` holds ONE mapping registry covering at least:
      `SyntacticValidationError→422`, `SignalNotFoundError→404`, `SignalIntervalUnconfiguredError→409`,
      `ProposalNotFoundError→404`, `ProposalNotOpenError→409`, and the maintenance validation
      error(s) currently mapped in `maintenance/service.py` — i.e. every domain exception any
      feature maps today, discovered by reading all 10 features, none invented. `install_error_handlers(app)`
      registers FastAPI exception handlers producing EXACTLY the current body shape
      (`{"detail": <same message text as today>}`) and status codes.
- [x] `composition/app.py::create_app` calls `install_error_handlers(app)`. After the strip, NO
      feature controller or feature service maps a domain exception to an HTTPException/status
      itself (grep-provable: no `HTTPException` construction inside `api/v1/{feature}/` except
      where a handler genuinely cannot apply — none expected).
- [x] `pyproject.toml` gains `api-shared-no-feature-imports` (proposal §6.3, verbatim: `_shared`
      forbidden from importing any of the 10 feature modules); `_shared` is NOT added to the
      `api-feature-independence` list. `lint-imports` exits 0 (**8 kept, 0 broken**).
- [x] **Frozen error contract:** ALL existing endpoint tests pass UNMODIFIED. Any edit to an
      existing endpoint test is a spec-review red flag requiring explicit justification.
- [x] `_shared/middleware.py` exists as a documented empty seam (docstring naming STORY-017 as the
      intended occupant, per proposal §6.2); no middleware logic in this story.
- [x] Backend six-gate DoD green; wiki blast radius resolved via the mechanical sweep (expect
      `api-five-file-convention.md` stale — revise it to "five files + `_shared`" per proposal §6.2
      and re-verify).

## Open Questions
None — admission criteria for `_shared` (cross-feature HTTP policy only) are in the proposal's
decision table (§6.4) and go into the wiki article revision.

## References
- Proposal: `docs/superpowers/specs/2026-07-10-api-restructure-design.md` §3.4 (G2, G5), §6.2–6.4, §10 Phase 2, §11 (risk: error-body drift)
- Depends on: STORY-074 (the meta-test must already knowingly exclude `_`-prefixed packages).

## History
- 2026-07-10: filed + refined from the accepted API restructure proposal (Phase 2). Status: ready (3 pts).
- 2026-07-10: Implemented in sprint-42. All tests passed, import linter verified, and wiki updated. final commit: `29ba79d` (and dependencies).
