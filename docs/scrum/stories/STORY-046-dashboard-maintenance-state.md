---
id: STORY-046
title: Dashboard maintenance-state display — the maintenance badge is currently unreachable
type: feature
---

## Context
From the 2026-07-02 full-codebase audit (M3). The frontend's health vocabulary includes
`maintenance` (`frontend/src/components/StatusBadge/StatusBadge.tsx::HealthStatus`, with tokens in
both themes), but the backend `ComponentStatus` enum (`core/domain/status.py`) is a closed set of
four values — operational / degraded / partial_outage / major_outage — with NO maintenance value.
`frontend/src/api/statusMapping.ts::toHealthStatus` therefore can never produce `maintenance` from
`GET /api/v1/components`: the Dashboard's maintenance badge is dead code today. Maintenance state
lives in a different concept entirely — maintenance WINDOWS (`GET /api/v1/maintenance`,
active/upcoming/past by `starts_at`/`ends_at`).

## Description
**Option A chosen (PO, 2026-07-06 sprint-37 refinement): frontend-only overlay, Dashboard
only.** The Dashboard also fetches `GET /api/v1/maintenance` and derives active windows
client-side (`starts_at <= now < ends_at`, the same derivation the Maintenance tab
already performs) keyed by `component_id`, overlaying a maintenance indicator per
component. No backend change; `ComponentDTO` stays `{id, name, status}`. Maintenance
display must follow the non-text-only color rule and never mask the underlying health
status (a component can be degraded AND under maintenance — dossier §6/§11 keep those
separate).

Consumer-DTO check (2026-07-06, at refinement): `MaintenanceWindowDTO` =
`{id, component_id, starts_at, ends_at, reason}` with tz-aware ISO datetimes and NO
server-side state field — active/upcoming/past is a client-side derivation, as 015f
already does. All fields the AC needs exist on the wire.

## Acceptance Criteria
- [ ] AC1: a component with an ACTIVE maintenance window (`starts_at <= now < ends_at`)
      is visibly marked as under maintenance on the Dashboard using the existing
      maintenance tokens; upcoming and past windows do NOT mark it. MSW-tested with
      active/upcoming/past fixtures derived from the real wire shape.
- [ ] AC2: the maintenance indicator coexists with (never replaces) the health status
      display — a degraded component under maintenance shows BOTH; indicator is not
      color-only.
- [ ] AC3: frontend three-gate DoD green (`npm test`, `npm run build`, `npm run lint`);
      backend untouched (empty backend diff); per-tab feature pattern respected.

## Open Questions
None — Option A and Dashboard-only both decided by the PO at sprint-37 refinement
(2026-07-06). An Availability-tab indicator is explicitly OUT; file a follow-up if it
ever proves useful.

## History
- 2026-07-02: drafted from audit finding M3. Status: draft (open design question). Rough estimate 2.
- 2026-07-06: refined at sprint-37 planning — PO chose Option A (frontend overlay) and
  Dashboard-only scope. Estimate confirmed 2. Status: ready.
