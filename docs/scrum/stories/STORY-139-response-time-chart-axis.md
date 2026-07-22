# STORY-139 — Response-time chart axis

- **Status:** ready
- **Points:** 3
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified in code (`deriveChartData.ts`,
`ResponseTimeChart.tsx`). The response-time chart's Y-axis ticks are data-derived
(max→min, e.g. 1082/809/536/262 — never 0), and labels render at `x=4`, only 4px above
their gridlines with no reserved gutter, so they overlay the plot/gridlines.

## Acceptance criteria
- **AC1** — The Y-axis uses a **0 baseline** (bottom tick = 0), not the data minimum.
- **AC2** — Ticks are **rounded "nice" numbers** (e.g. 0/250/500/750/1000-style), not raw
  data-derived values. Test asserts ticks are round multiples derived from a niced max.
- **AC3** — A **reserved axis gutter** offsets the plot so labels do not overlap gridlines
  or the plotted line at real data. Test asserts label x/y sit in the gutter, not over the plot.
- **AC4** — The empty/no-data state ("No response-time data available") and the chart's a11y
  labelling are unchanged.

## Design / skills
Honor the mandated skills. The chart is a bespoke SVG (not the minimal Sparkline). Keep the
tick-niceness logic pure and unit-tested (`deriveChartData`), separate from the SVG render.
Data-dependent visual → reality gate verifies the empty state live + the tick math via tests
over the plan's captured fixture (the live stack has no response-time data).
