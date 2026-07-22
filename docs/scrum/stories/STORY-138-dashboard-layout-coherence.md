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

## History
- sprint-61 (2026-07-22): **Deleted** the two divergent-ratio grid classes
  `.dashboard-page__mid-grid` (1.85fr/1fr) and `.dashboard-page__bottom-grid` (1.1fr/1fr),
  plus the `--side-stack` helper, from `DashboardPage.css`. Reason: they were the root cause
  of the jagged center gutter (AC1) — two rows on separate grids with different column ratios
  put the divider at different x-positions (measured ~145px jump). Replaced by ONE shared
  named-line grid `.dashboard-page__content-grid` (`[main-start] minmax(0,2fr) [main-end
  side-start] minmax(0,1fr) [side-end]`) whose columns are placed by grid-line name so a
  future edit cannot silently reintroduce a second ratio. `ComponentsRoster` moved from the
  old bottom grid into the side column (content rebalance, AC2). Commits 61d29cd/bcd0278/
  d9d0bf9; wiki recorded in `docs/scrum/wiki/frontend-zone.md` (2026-07-22).
