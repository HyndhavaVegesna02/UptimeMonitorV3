---
id: STORY-099
title: Signal quality — neutral zero-states, cross-tab awareness cards, last-updated, completeness label
type: story
---

## Context
ui-redesign exploration 2026-07-17 (journal findings #7, #8, #9): zero-value stat cards
keep alert colors (amber/orange/red "0" — false urgency, violates Grafana's meaningful-
color rule); the "Components" card duplicates "Operational N of N"; no last-updated
indicator anywhere despite background polling; the dashboard has no pending-approvals /
active-maintenance awareness; Availability's "8.33% • missing data" label reads as
"8.33% missing" when the number is completeness.

## Description
Dashboard (journal D4): status stat cards render neutral (muted) when their value is 0
and take their status color only when >0; replace the redundant "Components" card with
two action cards — "Pending approvals" (count, links to /approvals) and "Active/upcoming
maintenance" (count, links to /maintenance) — both neutral at 0; add a compact
"Updated Xs ago" indicator to the page header (shared PageHeader actions slot).
Availability: relabel completeness unambiguously ("N% of expected checks received",
bar semantics unchanged).

## Acceptance Criteria
- [ ] AC1: with all components Up, Degraded/Partial/Down cards render with neutral value
      color (verified via computed style); when a count >0 the status color returns.
- [ ] AC2: "Pending approvals" and "Maintenance" cards show live counts from the existing
      endpoints and navigate to their tabs on click (entire card is the interactive
      element, keyboard-focusable, cursor-pointer).
- [ ] AC3: a last-updated indicator renders on Dashboard, updates with the poll cycle,
      and never shows a raw ISO string.
- [ ] AC4: Availability data-completeness column header/value/label can no longer be read
      as "N% missing" (copy per description); legend unchanged.
- [ ] AC5: Vitest for card color logic, count wiring (MSW), and the relabel; suite green.

## History
- 2026-07-17: filed + refined during ui-redesign refinement (PO-delegated); estimate 2.
