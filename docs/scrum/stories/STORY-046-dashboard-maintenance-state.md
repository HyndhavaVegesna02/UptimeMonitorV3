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

## Description (design decision needed — hence draft)
Decide and implement how the Dashboard shows "this component is under maintenance right now":
- Option A (frontend-only): the Dashboard also fetches `/maintenance` and overlays an active-window
  indicator per component (badge or secondary marker) — no backend change; two fetches per view.
- Option B (backend): the components read model / DTO gains a derived `under_maintenance: bool`
  (computed from active windows at read time) — one fetch, but a DTO change.
Either way: maintenance display must follow the non-text-only color rule and never mask the
underlying health status (a component can be degraded AND under maintenance — dossier §6/§11 keep
those separate).

## Acceptance Criteria (to firm up once the option is chosen)
- [ ] AC1: a component with an ACTIVE maintenance window is visibly marked as under maintenance on
      the Dashboard (badge/indicator using the existing maintenance tokens); upcoming/past windows
      do not mark it. Tested via MSW with active/upcoming/past fixtures.
- [ ] AC2: maintenance display coexists with (never replaces) the health status display.
- [ ] AC3: gates green; per-tab pattern respected.

## Open Questions
- Option A vs B (PO/design call — affects whether this is frontend-only or touches the API).
- Should the same indicator appear on the Availability tab (maintenance verdicts are already
  excluded from the availability math per dossier §11)?

## History
- 2026-07-02: drafted from audit finding M3. Status: draft (open design question). Rough estimate 2.
