---
id: STORY-014
title: Five-file feature modules
type: feature
---

## Context
Spec: dossier §13 (five-file API convention). Zone 6. The edge's shape; the boundary
governs where logic lives. Edge `service.py` stays thin and delegates inward.

## Description
Each FastAPI feature at `api/v1/<feature>/` = `__init__.py` / `controller.py` (routes,
scopes, status codes, no logic) / `models.py` (pydantic HTTP DTOs only) / `validation.py`
(syntactic input checks, stdlib only) / `service.py` (THIN: validate → call a core service
via the composition container → shape the HTTP result; never another feature's service).
Endpoints for the six tabs' data + the decision/approve endpoint. No horizontal feature
imports (enforceable as a fourth linter contract).

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Each feature follows the five-file shape per §13.
- [ ] AC2: `lint-imports` confirms no cross-feature imports (`api.v1.<a>` may not import
      `api.v1.<b>`).
- [ ] AC3: The edge holds no business logic — real logic stays in `core/services/`;
      canonical types stay in core (edge exposes DTOs, not domain types).
- [ ] AC4: Endpoints serve the six tabs' data + the decision endpoint; tests cover each.

## Open Questions
- Confirm the endpoint list per tab and whether the no-cross-feature rule becomes a 4th
  import-linter contract here.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §13. Status: draft — refine before its sprint.
