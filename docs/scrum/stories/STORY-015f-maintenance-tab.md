---
id: STORY-015f
title: Maintenance tab — schedule + window state
type: feature
---

## Context
Spec: dossier §17 + the maintenance feature (STORY-036). Zone 7. Depends on STORY-015a (shell). Shows
maintenance windows (scheduled/active/past) and their effect on component status.

## Acceptance Criteria
- [ ] AC1: Lists maintenance windows from `GET /api/v1/maintenance` (component, start/end, state:
      scheduled/active/ended) with clear state badges and tz-aware times.
- [ ] AC2: Loading/empty/error states; MSW-backed Vitest tests cover success/empty/error. (Window
      create/edit is out of scope unless the backend exposes it — read-first; flag if a mutation is wanted.)
- [ ] AC3: a11y + responsive floor met; state not conveyed by color alone.

## Skills to use
Design source: `DESIGN-airtable.md` (reuse the shell's token layer; window state badges use the health/
semantic tokens, not new colors).
`ui-ux-pro-max` (status/badges, forms if a mutation lands), `vercel-react-best-practices`, `design-taste-frontend`.

## History
- 2026-06-29: created as a per-tab split-child of STORY-015. 3 pts. Status: ready.
