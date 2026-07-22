# STORY-143 — Component-scoped availability view

- **Status:** ready
- **Points:** 5
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified in code. The pinned "HTTP Check" nav item
hardcodes `path="/availability"` (`Sidebar.tsx:142`) — the generic list for every pin — and
no component-scoped route exists (`routes.tsx` has only `availability`). Consumes the
already-live `GET /availability/component/{id}` contract (verified this sprint-line by
STORY-129).

## Acceptance criteria
- **AC1** — A **component-scoped availability route** exists (e.g. `/availability/:componentId`)
  rendering that one component's availability (rollup + per-signal drill-down) on the real
  `GET /availability/component/{id}` data.
- **AC2** — The pinned nav item routes to that **component-scoped view**, not the generic list.
  Test asserts the pinned item's target.
- **AC3** — The view handles **loading / error+retry / empty / unknown-component** states (a
  bad id → a clean not-found treatment, not a crash or infinite spinner).
- **AC4** — Back-navigation to the generic Availability list works; the generic list is
  unchanged.
- **AC5** — Reality gate: navigate via the pinned item to the scoped view on the live stack;
  exactly one h1; no horizontal body scroll @390 + @1440; zero console errors.

## Design / skills
Honor the mandated skills. Reuse the existing `ComponentAvailabilityCard` / availability
feature components where they fit; the scoped view is a fresh page composition, not a copy of
the list page. Largest story — do last (natural carryover if the review tail runs long).
