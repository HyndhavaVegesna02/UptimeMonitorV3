---
id: STORY-096
title: Responsive shell — adaptive sidebar (rail ≤1024px, drawer ≤768px) and mobile-safe layouts
type: story
---

## Context
Found by the STORY-095 Playwright sweep (sprint-51, 2026-07-17): at 390×844 the nav
sidebar keeps its full desktop width, squeezing page content into a narrow column.
Re-verified 2026-07-17 by the ui-redesign exploration (journal findings #1–#3,
`docs/scrum/ui-redesign/exploration/explore-17/18.png`): it affects every page, the
sample-mode banner wraps into a tall column, and a horizontal scrollbar appears.

## Description
Give the shell adaptive navigation (journal decision D2, Material adaptive-navigation):
- ≤1024px: sidebar auto-collapses to the existing icon rail (user can still expand).
- ≤768px: sidebar becomes an overlay drawer, closed by default, opened from a hamburger
  button in the top bar; scrim behind it; Escape and scrim-click close it.
- Content column, banner, filter rows, and tables must fit 390px with no horizontal
  page scroll (tables may scroll inside their own container per the density rules).

## Acceptance Criteria
- [ ] AC1: at 390×844 no page has a horizontal page-level scrollbar
      (`document.documentElement.scrollWidth <= 390` on all six tabs).
- [ ] AC2: at 390×844 the nav is an overlay drawer — closed by default (content ≥ 90% of
      viewport width), opened via a visible labeled button, closable via scrim click and
      Escape; focus moves into the drawer on open and returns to the trigger on close.
- [ ] AC3: at 1024–1440px behavior is unchanged from today except the ≤1024px auto-rail;
      at ≥1280px the expanded sidebar renders exactly as today.
- [ ] AC4: the sample-mode banner lays out on one or two lines at 390px (no tall wrap).
- [ ] AC5: Vitest coverage for drawer open/close/focus behavior; existing suite stays green.

## Open Questions
(resolved at refinement 2026-07-17: rail at ≤1024px, overlay drawer at ≤768px — journal D2;
breakpoint tokens added as CSS custom properties, not magic numbers.)

## History
- 2026-07-17: filed from the sprint-51 review (STORY-095 finding; PO approved filing).
- 2026-07-17: refined for the ui-redesign initiative (PO-delegated); estimate 3.
