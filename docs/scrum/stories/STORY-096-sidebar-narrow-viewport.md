---
id: STORY-096
title: Sidebar keeps desktop width below ~768px — add a narrow-viewport breakpoint
type: story
---

## Context
Found by the STORY-095 Playwright sweep (sprint-51, 2026-07-17): at 390×844 the nav
sidebar keeps its full desktop width, squeezing page content into a narrow column.
Renders without errors — a layout/UX gap, not a defect. Evidence:
`docs/scrum/sprints/2026-07-17-sprint-51/ui-sweep/` (390px screenshot + findings.md).

## Description
Give the shell a narrow-viewport breakpoint: below a chosen width the sidebar collapses
(icon rail, drawer, or top-bar pattern — decide at refinement against the design brief
`DESIGN-linear.app.md` adaptation rules and the sprint-38 Operator Dashboard re-skin).

## Acceptance Criteria (draft — refine before sprinting)
- [ ] AC1: at 390px width, page content occupies the majority of the viewport; the nav
      remains reachable (collapsed pattern TBD at refinement).
- [ ] AC2: desktop layout (≥ the chosen breakpoint) is pixel-unchanged.
- [ ] AC3: Vitest coverage for the breakpoint behavior; the ui-sweep harness's 390px
      check passes without the squeeze finding.

## Open Questions
- Which collapse pattern (icon rail vs drawer)? Which breakpoint token?

## History
- 2026-07-17: filed from the sprint-51 review (STORY-095 finding; PO approved filing).
  Draft — needs refinement + estimate.
