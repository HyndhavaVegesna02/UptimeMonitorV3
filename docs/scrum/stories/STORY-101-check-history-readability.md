---
id: STORY-101
title: Check History readability — column diet, latency encoding, sticky header, result count
type: story
---

## Context
ui-redesign exploration 2026-07-17 (journal finding #13): Type and Component columns are
identical on every row of the seeded reality (Type is per-signal, Component repeats);
the timestamp column is ~2× its needed width; latency is a bare number with no visual
encoding; there's no row-count/result summary; the header scrolls away on long lists.

## Description
Display-layer table improvements (endpoint and DTOs untouched):
- Merge Type into the Component cell (secondary text) — drops one column.
- Latency gets a quiet visual encoding: tabular figures + a threshold tint (e.g. muted
  under 500ms, amber 500–1000ms, red above — thresholds as named tokens, not magic
  numbers in JSX).
- Sticky table header within the table's scroll container.
- A results summary line ("N checks · M down" + active-filter echo) above the table,
  which is also the aria-live region for filter changes.
- Timestamp column sized to the STORY-098 relative format.

## Acceptance Criteria
- [ ] AC1: table renders without the redundant standalone Type column; signal type still
      visible per row (secondary text).
- [ ] AC2: latency cells carry threshold-based styling driven by tokens; verified via
      computed style at each threshold via MSW fixtures.
- [ ] AC3: header row remains visible while scrolling the table body (sticky within the
      table container).
- [ ] AC4: summary line shows total and down counts and reflects active filters;
      announced via aria-live="polite" on filter change.
- [ ] AC5: 390px: table scrolls horizontally inside its own container only (no page
      scroll; STORY-096 AC1 preserved); Vitest green.

## History
- 2026-07-17: filed + refined during ui-redesign refinement (PO-delegated); estimate 2.
