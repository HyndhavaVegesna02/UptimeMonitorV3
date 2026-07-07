---
id: STORY-055
title: Design-system foundation — Geist fonts, retuned tokens, 7-status palette, shadow token, icon set, restyled base components + shared primitives
type: feature
---

## Context
Sprint 38 redesigns the operator SPA to the imported *Operator Dashboard* mock
(`docs/scrum/sprints/2026-07-07-sprint-38/reference-operator-dashboard.dc.html`). This story is
Wave 0 — the shared substrate every other story inherits: it must land gate-green + committed on
`sprint-38` before 056 or any Wave-2 page. Full token mapping tables, the palette, and the
primitive specs are in this sprint's `plan.md` (§"Design system spec") — build to that + the mock.

## Description
Retune the design tokens to the reference (keeping token NAMES + the `data-theme` scoping + the
`index.html` pre-paint script), self-host Geist, extend the status palette 5→7, add a shadow token
and an inline icon set, restyle the existing base components, and build the four shared
presentational primitives Wave-2 consumes. Frontend-only; empty backend diff.

## Acceptance Criteria
- [ ] AC1: `tokens.css` retuned to the reference palette for BOTH themes per plan.md's remap table
      (canvas/surface ladder/hairlines/ink/accent + new `--color-accent-bg`); `data-theme` scoping
      and the pre-paint script mechanism unchanged. Existing theme tests stay green.
- [ ] AC2: Status palette extended to 7 — `partial` + `missing` added (dark+light + `-subtle`);
      `HealthStatus` union + `StatusBadge` `DEFAULT_LABELS` extended; `statusMapping.ts` maps
      `partial_outage → 'partial'`. Every badge remains dot **+ text label**, never color-only.
      StatusBadge + statusMapping tests updated to drive the new values.
- [ ] AC3: Geist + Geist Mono self-hosted via `@fontsource/geist` + `@fontsource/geist-mono`
      (imported in `main.tsx`; Inter/JetBrains imports + deps removed); `--font-sans`/`--font-mono`
      point to Geist; NO Google-CDN link; `tabular-nums` global; type scale retuned per plan.md.
      `package.json` + the CLAUDE.md/README font line updated in the same commit.
- [ ] AC4: `--shadow` token added (none dark / subtle light) and an inline `Icon` component/set
      (feather-style SVGs used across the redesign) added; `Button`/`Panel`/`Loading`/`Error`/
      `Empty` restyled to the new tokens with their existing tests green (accessible names unchanged).
- [ ] AC5: Shared primitives built with co-located CSS + Vitest tests, token-only colors:
      `Table`/`DataGrid` (role="table", `<th scope="col">`), `UptimeBar` (segment sparkline + no-data
      state), `SummaryCard` (dot+label+mono value+sub), `Timeline` (line+dot list).
- [ ] AC6: Frontend three-gate DoD green (`npm test`, `npm run build`, `npm run lint`); empty
      backend diff; wiki staleness sweep resolved (`frontend-zone` article re-verified/updated).

## Open Questions
None — token values, palette, fonts, and primitive specs pinned in plan.md at planning.

## History
- 2026-07-07: drafted + refined at sprint-38 planning; re-pointed 3→5 to pull the shared primitives
  forward so Wave-2 pages can be built in parallel. Status: ready. PO-approved.
