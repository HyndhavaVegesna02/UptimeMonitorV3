---
id: STORY-060
title: Check History redesign — filter toolbar (search + result + location), dense mono grid; resolve STORY-054 flaky render
type: feature
---

## Context
Wave 2 (parallel). Depends on 055 (`Table`) + 056. Rebuilds `pages/CheckHistoryPage.tsx` +
`features/history/*` to the mock's toolbar + dense grid (plan.md §"Check History"). Subsumes
STORY-054 (the flaky 1000-cap render under `npm test` parallelism).

## Acceptance Criteria
- [ ] AC1: Filter toolbar — a search input (client-side filter over component/location/signal_key) +
      a result-filter `<select>` + a location-filter `<select>`, plus the existing 24h/7d/30d window
      toggle (`windowRange`). All controls labeled (accessible names).
- [ ] AC2: Dense mono grid: Timestamp / Component / Location / Result (dot+label) / Latency, via the
      existing `useHistory` + `observationHealth`. "Type" and HTTP "Code" columns are OMITTED (not on
      `ObservationDTO`) → STORY-064. The "showing latest N of M" cap caption is kept.
- [ ] AC3: The rebuilt table does NOT false-red under `npm test` file-parallelism (STORY-054
      resolved) — e.g. bounded/virtualized render or a smaller-but-representative fixture — and
      `npm test` passes deterministically. Note the resolution in the story History.
- [ ] AC4: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None — HTTP code / check-type columns deferred to STORY-064.

## History
- 2026-07-07: drafted + refined at sprint-38 planning; subsumes STORY-054. Status: ready. PO-approved.
