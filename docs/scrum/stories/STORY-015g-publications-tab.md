---
id: STORY-015g
title: Publications tab — Statuspage publish history
type: feature
---

## Context
Spec: dossier §17 + the publications feature (STORY-037). Zone 7. Depends on STORY-015a (shell). Shows the
history of status changes published to Statuspage.

## Acceptance Criteria
- [ ] AC1: Lists publications from `GET /api/v1/publications` (most-recent first): component, status,
      published_at, proposal id, with tz-aware times.
- [ ] AC2: Loading/empty/error states; MSW-backed Vitest tests cover success/empty/error.
- [ ] AC3: a11y + responsive floor met.

## Skills to use
Design source: `DESIGN-airtable.md` (reuse the shell's token layer; publish-history list uses hairline
dividers + `body-md` rows).
`ui-ux-pro-max` (data lists), `vercel-react-best-practices`, `design-taste-frontend`.

## History
- 2026-06-29: created as a per-tab split-child of STORY-015. 2 pts. Status: ready.
