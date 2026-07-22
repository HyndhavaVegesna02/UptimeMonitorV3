# STORY-138 — Dashboard layout coherence

- **Status:** ready
- **Points:** 5
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified live (measured). The Dashboard's two
content rows use **separate grids** — `mid-grid 1.85fr/1fr` vs `bottom-grid 1.1fr/1fr` —
so the center gutter jumps ~145px between rows (the headline visual bug). Related: a large
bottom-right empty void (`align-items:start` + short right column), uneven KPI card bottom
padding (cards 1–2 have a sparkline, 3–4 leave an empty band), and an inconsistent KPI
accent bar (green on one card, blue on another, none on others).

## Acceptance criteria
- **AC1** — The two content rows share **one 2-column grid** with a single consistent
  gutter x-position across both rows (no ~145px jump). Reality gate measures both rows' card
  edges; the divider x matches within a small tolerance.
- **AC2** — Column heights are balanced so there is **no large bottom-right empty void** —
  equal-height columns or a deliberate content rebalance that fills the region (not a stretch
  hack leaving whitespace).
- **AC3** — All four KPI cards have a **consistent content footprint** — cards without a
  sparkline no longer leave a visibly empty band vs cards with one.
- **AC4** — KPI accent treatment is **consistent by rule** (deliberate — a bar per card tied
  to meaning, or none — not an accidental green/blue/none mix).
- **AC5** — Responsive: the shared grid collapses cleanly at mobile (390) with no horizontal
  body scroll. Reality-gate visual @390 + @1440.

## Design / skills
This is the highest-visibility story — fresh, high-craft layout on the sprint-59 system.
Honor `ui-ux-pro-max`, `web-design-guidelines`, `emil-design-eng`, `design-system`. Use
design-system spacing tokens, not raw px. Make the grid decision principled (one grid,
named columns), not a per-row patch.
