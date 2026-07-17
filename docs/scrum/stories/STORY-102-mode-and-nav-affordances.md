---
id: STORY-102
title: Mode & nav affordances — labeled sample-mode control, persistent mode indicator, rail tooltips, form feedback
type: story
---

## Context
ui-redesign exploration 2026-07-17 (journal findings #12, #15, #16): the sample-mode
toggle is an icon-only lightning button styled red (reads as alert/destructive, not an
environment switch); dismissing its banner leaves the red icon as the only indicator;
the collapsed sidebar rail has no tooltips and its badge degrades to an unexplained dot;
the maintenance form relies on native validation bubbles, Title isn't required, and
creation gives no success feedback.

## Description
- Sample-mode control: labeled switch ("Sample mode") in the top bar, amber/warning
  accent when ON (not red); when ON and the banner is dismissed, a compact persistent
  "SAMPLE" chip remains in the top bar (clicking re-opens the banner).
- Collapsed rail: accessible tooltips (name + pending count) on icon-only nav items;
  the dot badge gets an aria-label with the count.
- Maintenance form: inline styled validation (message below field, aria-describedby,
  focus to first invalid on submit), Title required, success toast (aria-live polite,
  auto-dismiss) after create/delete.
- Theme toggle gains a tooltip naming the action.

## Acceptance Criteria
- [ ] AC1: sample-mode control shows a visible text label at ≥768px and an aria-label
      always; OFF state is neutral, ON state is warning-accented (computed styles).
- [ ] AC2: with sample mode ON and banner dismissed, a persistent indicator remains
      visible in the top bar on all tabs and restores the banner on click.
- [ ] AC3: collapsed rail items expose tooltips on hover AND focus (title or custom,
      keyboard-reachable); badge has an aria-label with the count.
- [ ] AC4: maintenance form: submitting invalid shows styled inline errors below the
      fields (no native bubbles), focus moves to the first invalid field, Title is
      required; successful create/delete raises a polite toast.
- [ ] AC5: Vitest for toggle states, indicator persistence, tooltip a11y, and form
      validation; suite green.

## History
- 2026-07-17: filed + refined during ui-redesign refinement (PO-delegated); estimate 2.
