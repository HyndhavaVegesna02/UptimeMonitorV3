# STORY-140 — Empty-state & data-formatting polish

- **Status:** ready
- **Points:** 3
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified. Three items: KPIs render a bare "— %" /
"— ms" + "Across 0 probe locations" instead of a clean empty treatment (confirmed live);
History-row timestamps carry no timezone label (the Maintenance card already shows "UTC");
location labels are cryptic ("…0047"). NOTE: true human-readable location names require a
backend field that does not exist (`location_name`) — that is out of frontend scope and is
filed as STORY-144; this story only improves the client-side treatment.

## Acceptance criteria
- **AC1** — A KPI with no data renders a **clean "No data yet" treatment**, not a bare
  "— %" / "— ms" + "Across 0 probe locations". Consistent across the availability and
  response-time KPIs. Verified live against the current empty stack.
- **AC2** — History-row timestamps carry an explicit **timezone indicator** consistent with
  the Maintenance card's "UTC". Test asserts the tz label is present in the rendered string.
- **AC3** — Location labels get a **cleaner frontend-scope treatment** than "…0047" (a
  readable short-id presentation). A doc-comment + the story History record that **true names
  are blocked on a backend field** (filed STORY-144). This story does NOT invent names
  client-side.
- **AC4** — Gates green; no regression.

## Design / skills
Honor the mandated skills. The "No data yet" treatment should reuse/extend the design-system
EmptyState idiom at the KPI grain, not a one-off string.
