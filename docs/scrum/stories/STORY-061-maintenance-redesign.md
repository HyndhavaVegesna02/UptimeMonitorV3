---
id: STORY-061
title: Maintenance redesign — two-column form-card + windows list with state badges, inline 422 field mapping preserved
type: feature
---

## Context
Wave 2 (parallel). Depends on 055 + 056. Rebuilds `pages/MaintenancePage.tsx` +
`features/maintenance/*` to the mock's two-column layout (plan.md §"Maintenance"). Preserves the
inline 422 field-error mapping (`fieldError`) and window-state derivation (`windowState`).

## Acceptance Criteria
- [ ] AC1: Two-column layout — a form card (Title, Component `<select>`, Start/End `datetime-local`,
      "Schedule window" submit) on the left + a windows list on the right (title + state badge via
      `deriveWindowState` + `component · range`). "Title" maps to the real `reason` field (the DTO has
      no separate title).
- [ ] AC2: Inline field-level 422 errors preserved via `fieldErrorFromDetail` (⚠ + ink text) with the
      form-level fallback; form resets on success; `postMaintenance`/`getMaintenance` unchanged.
- [ ] AC3: The per-window delete button is OMITTED (no DELETE endpoint) → STORY-065.
- [ ] AC4: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None — maintenance title field + DELETE endpoint deferred to STORY-065.

## History
- 2026-07-07: drafted + refined at sprint-38 planning. Status: ready. PO-approved.
