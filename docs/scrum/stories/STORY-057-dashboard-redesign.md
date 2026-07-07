---
id: STORY-057
title: Dashboard redesign — summary stat cards + grouped expandable component rows + signal drill-down + uptime sparkline (adapt to real data)
type: feature
---

## Context
Wave 2 (parallel). Depends on 055 (primitives: `SummaryCard`, `UptimeBar`, `Table`) + 056 (shell,
sample-mode relocated). Rebuilds `pages/DashboardPage.tsx` + `features/dashboard/*` to the mock's
Dashboard (plan.md §"Dashboard"). Adapt to real data — no fakes.

## Acceptance Criteria
- [ ] AC1: A row of `SummaryCard`s derived from `getComponents` (counts by status) — real data only.
- [ ] AC2: Component rows restyled; expandable (keyboard-operable, `aria-expanded`) to show the
      signals feeding the component from `getTopology` + `getHistory` (location / status / latency /
      last-observed). Graceful degradation on any fetch failure.
- [ ] AC3: Per-row uptime % + an `UptimeBar` sparkline bound to real availability/history; where no
      data exists the bar is OMITTED gracefully (NO fabricated segments). Rendered under ONE group
      (no `group` field on the wire → STORY-067).
- [ ] AC4: The active-maintenance badge (STORY-046 behavior — `useMaintenanceWindows` +
      `deriveWindowState`, dot+label, coexists with health, never color-only) is preserved.
- [ ] AC5: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None — component grouping + a dedicated uptime-bucket API are deferred to STORY-067; this story
adapts to what `getComponents`/`getTopology`/`getHistory`/`getComponentAvailability` provide.

## History
- 2026-07-07: drafted + refined at sprint-38 planning. Status: ready. PO-approved.
