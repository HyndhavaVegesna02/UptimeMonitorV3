---
id: STORY-065
title: Maintenance title field + DELETE endpoint
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Maintenance form has a
"Title" field and each window row has a delete button. `MaintenanceWindowDTO` has `reason` (no
title) and the API exposes only `GET`/`POST /v1/maintenance` (no DELETE). STORY-061 maps
title↔reason and omits delete; this story adds the real capability.

## Description (to refine)
Add an optional `title` to the maintenance window model/DTO (distinct from `reason`) and a
`DELETE /v1/maintenance/{id}` endpoint (five-file conventions; repository delete; 404 on unknown).
Then the frontend adds a real Title field + a delete action (with the no-dialog constraint honored).

## Acceptance Criteria (to refine)
- [ ] Add `title` (migration + DTO + validation) and `DELETE` (endpoint + repo method + 404 test).
- [ ] Frontend: real Title field + delete button wired.

## Open Questions
- Is `title` worth a schema column, or is `reason` sufficient long-term? (PO call at refinement.)

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
