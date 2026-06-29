---
id: STORY-015d
title: Availability tab — two-grain availability + group rollup
type: feature
---

## Context
Spec: dossier §17 + §11 (availability-vs-status separation). Zone 7. Depends on STORY-015a (shell).
Shows availability percentages per component and the group rollup over a window.

## Acceptance Criteria
- [ ] AC1: Renders availability from `GET /api/v1/availability` (per-component + rollup), formatted with
      tabular figures (`number-tabular`) and locale-aware percentages.
- [ ] AC2: Loading/empty/error states; MSW-backed Vitest tests cover success/empty/error.
- [ ] AC3: If a chart is used, it follows the `ui-ux-pro-max` chart rules (legend, accessible colors,
      empty-data state, text alternative). Responsive + a11y floor met.

## Skills to use
`ui-ux-pro-max` (charts & data, number formatting), `vercel-react-best-practices`, `design-taste-frontend`.

## History
- 2026-06-29: created as a per-tab split-child of STORY-015. 3 pts. Status: ready.
