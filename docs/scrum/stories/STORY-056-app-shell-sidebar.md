---
id: STORY-056
title: App shell redesign — collapsible left icon sidebar, top bar (theme toggle + relocated sample-mode trigger), banner, Approvals count badge
type: feature
---

## Context
Wave 1 — the shell every page renders inside. Depends on STORY-055 (tokens/icons). Replaces the
current top-nav (`frontend/src/nav/Nav.tsx` + `AppShell.tsx`) with the mock's collapsible left icon
sidebar + top bar. Layout spec in this sprint's plan.md (§"Shell"). It precedes STORY-057 because it
relocates the sample-mode toggle OUT of `DashboardPage` (which 057 rebuilds).

## Description
Build the sidebar + top-bar shell, relocate the sample-mode control to the top bar, wire the
banner + Approvals count badge. Preserve routing (`tabs.ts` stays the single nav source), the
skip-link, theme toggle behavior, and accessibility.

## Acceptance Criteria
- [ ] AC1: Collapsible left icon sidebar replaces the top nav — logo+collapse header, one
      icon+label button per tab (real routed `NavLink`s; active = accent), collapse-to-icons state.
      Collapse toggle has `aria-expanded` + a dynamic `aria-label`. Skip-link + 40px targets kept.
- [ ] AC2: Top bar (right-aligned) with the theme toggle + a ⚡ trigger wired to the EXISTING
      sample-mode API (`useSampleMode`/`putSampleMode` semantics preserved, incl. `role`+state);
      the Dashboard's inline sample-mode switch is removed (moved here).
- [ ] AC3: Dismissible banner region under the top bar shows the sample-mode-on warning
      (`role="status"`/`alert` preserved).
- [ ] AC4: The Approvals sidebar item shows a live pending-count badge (dot when collapsed / number
      when expanded) from `getApprovals`; degrades gracefully (no badge) on fetch failure.
- [ ] AC5: `tabs.ts` remains the single source consumed by sidebar + routing; all shell/nav tests
      updated to the new structure (by role/name).
- [ ] AC6: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None.

## History
- 2026-07-07: drafted + refined at sprint-38 planning. Status: ready. PO-approved.
