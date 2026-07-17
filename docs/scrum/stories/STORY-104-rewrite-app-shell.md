---
id: STORY-104
title: Rewrite shell — top command bar, horizontal tab nav, responsive sheet, mode controls
type: story
---

## Context
Brief (`docs/scrum/ui-rewrite/design-brief.md` §IA): the rewrite deliberately abandons the
left sidebar. Depends on STORY-103's primitives/tokens.

## Description
New `AppShell`: slim top command bar — brand + live overall-status dot (worst-of component
statuses), horizontal tab nav (6 tabs, active indicator), right cluster: sample-mode
labeled switch (neutral OFF / amber ON, never red) + persistent SAMPLE chip when banner
dismissed + banner (ported contract), theme toggle, "Updated Xs ago". ≤768px: nav collapses
to a hamburger-opened sheet/drawer with the ported focus-trap contract (closed default,
focus in/return, Escape + scrim + nav-click close). Skip link + one `<main>` landmark.
Routing table unchanged (6 routes); pages render as placeholders on new tokens until their
own stories.

## Acceptance Criteria
- [ ] AC1: all six routes render inside the new shell; NO sidebar in the DOM; tab nav
      reflects the active route (aria-current), keyboard operable.
- [ ] AC2: overall-status dot derives worst-of from the components endpoint and carries an
      accessible label naming the state.
- [ ] AC3: sample-mode control + chip + banner behaviors match the ported contracts
      (switch semantics, chip appears only ON+dismissed, chip restores banner) — Vitest.
- [ ] AC4: ≤768px sheet nav passes the focus contract (Vitest) and 390px has no page-level
      horizontal scroll on any route (live gate).
- [ ] AC5: three frontend gates exit 0; zero console errors on clean load of all six routes
      (live gate).

## History
- 2026-07-18: filed at ui-rewrite refinement (PO-delegated); estimate 3.
