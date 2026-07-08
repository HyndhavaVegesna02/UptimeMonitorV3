---
id: STORY-058
title: Availability redesign — grid layout, segment bars + hatched completeness + legend, window toggle, per-signal drill-down
type: feature
---

## Context
Wave 2 (parallel). Depends on 055 (`UptimeBar`) + 056. Rebuilds `pages/AvailabilityPage.tsx` +
`features/availability/*` to the mock's grid (plan.md §"Availability"). Reuses existing
`windowRange` + `format` logic.

## Acceptance Criteria
- [ ] AC1: Grid layout (Component | Availability | Data completeness). Availability cell = big mono
      % + down label + `UptimeBar`. Completeness cell = big mono % + "missing data" chip when low +
      split bar (`--color-health-up` width = completeness, remainder hatched `missing`).
      `availability_pct`/`completeness_pct` are 0-1 FRACTIONS — rendered via existing `formatPct`
      (no scale change). Down/missing legend present.
- [ ] AC2: 24h/7d/30d window toggle reuses `windowRange` (`aria-pressed` kept); per-signal
      drill-down preserved; fixtures derive from the existing availability MSW handler.
- [ ] AC3: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None.

## History
- 2026-07-07: drafted + refined at sprint-38 planning. Status: ready. PO-approved.
