---
id: STORY-015d
title: Availability tab — two-grain availability + group rollup over a window
type: feature
---

## Context
Spec: dossier §17; availability math from STORY-011 (two-grain + group rollup), exposed by
`GET /api/v1/availability` (STORY-014c). Zone 7. Split-child of STORY-015; depends on
STORY-015a.

## Description
Per-component availability over a selectable time window (e.g. 24h / 7d / 30d presets mapped
to tz-aware `since`/`until` query params), plus the group rollup. Percentages are the headline
(mono, one decimal); a simple horizontal bar per component gives shape without a charting
library. Window changes refetch.

## Acceptance Criteria
- [ ] AC1: The tab fetches `GET /api/v1/availability` with tz-aware `since`/`until` derived
      from a window selector (at least 24h / 7d / 30d) and renders per-component availability
      + the group rollup.
- [ ] AC2: Percentages render with consistent precision in mono type; each row carries a
      non-text visual cue (bar) that is not the only carrier of the information (value is
      text). Bar styling uses tokens.
- [ ] AC3: Changing the window refetches and re-renders; tested via MSW (assert the query
      params actually sent are tz-aware and match the selected window).
- [ ] AC4: Loading/empty/error+retry states tested.

## Open Questions
None.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction. Status: ready. Estimate 3.
