---
id: STORY-066
title: Publication author / outcome / incident metadata
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Publications timeline
shows an author, an outcome chip, and an incident reference. `PublicationDTO` is
`{id, component_id, status, published_at, proposal_id?}` — none of those. STORY-062 omits them;
this story adds the real data.

## Description (to refine)
Capture + expose the publish actor (author), the Statuspage publish outcome (success/failure/…),
and any incident id created, on the publication record + `PublicationDTO`. Then the frontend adds
them to the timeline rows.

## Acceptance Criteria (to refine)
- [ ] Determine what the publish adapter already records (actor, Statuspage response, incident id).
- [ ] Extend the publication model/DTO with the available fields; tests.
- [ ] Frontend: render author/outcome/incident in the Publications timeline.

## Open Questions
- Does the Statuspage publish path capture an actor + incident id today, or is that new?

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
