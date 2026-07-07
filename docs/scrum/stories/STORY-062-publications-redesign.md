---
id: STORY-062
title: Publications redesign — vertical timeline layout (adapt to real data)
type: feature
---

## Context
Wave 2 (parallel). Depends on 055 (`Timeline`) + 056. 2 pts → gate-only (no reviewers). Rebuilds
`pages/PublicationsPage.tsx` + `features/publications/*` to the mock's vertical timeline (plan.md
§"Publications").

## Acceptance Criteria
- [ ] AC1: Vertical `Timeline` layout — dot + connector per row; scope (component name) → status
      (via `toHealthStatus`); `published_at` (mono) + `proposal_id` (em-dash when null), most recent
      first. Author/outcome/incident are OMITTED (not on `PublicationDTO`) → STORY-066.
- [ ] AC2: The "Showing the latest 50 publications" caption is kept; empty/loading/error states via
      the shell primitives.
- [ ] AC3: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None — publication metadata deferred to STORY-066.

## History
- 2026-07-07: drafted + refined at sprint-38 planning. Status: ready. PO-approved.
