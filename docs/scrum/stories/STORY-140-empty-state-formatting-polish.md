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

## History
- 2026-07-22 (implementer): AC1 — `EmptyState` gained a `compact` modifier (no block padding,
  left-aligned) so it can embed inside a `SummaryCard`'s value area; `SummaryCard` gained an
  `empty?: { message; detail? }` prop that swaps the value/unit/sub block for a compact
  `EmptyState` when a KPI's underlying value is genuinely `null` (a degenerate no-data window).
  `KpiRow`'s availability and response-time cards now render "No data yet" via this prop instead
  of a bare "— %"/"— ms" plus a misleading "Across 0 probe locations" sub line.
- 2026-07-22 (implementer): AC2 — `formatObservedAt` (History grid's timestamp column) now
  appends an explicit `" UTC"` label, matching the convention `formatWindowRange` (Maintenance
  card) already established for its own hand-formatted (`getUTC*`) fields. Confirmed
  `formatObservedAt` was already formatting UTC fields (never `toLocaleString`), so the "UTC"
  label is truthful, not a guess.
- 2026-07-22 (implementer): AC3 — `locationLabel` now renders a `#`-prefixed short id (`#0047`)
  instead of the ellipsis-prefixed tail (`…0047`) — a readable "deliberate short id" idiom (same
  as a ticket/PR number) rather than "truncated, something hidden". **True human-readable
  location names remain blocked**: the `/api/v1` `ObservationDTO.location` field is a raw
  synthetic-location id with no accompanying name, and this story does NOT invent one
  client-side. The real fix — a backend `location_name` field — is filed as **STORY-144**
  (backend, not in this sprint's scope). Recorded here per the checklist's "drops/blocks a
  user-facing capability" rule, and as a doc-comment on `locationLabel.ts` itself.
