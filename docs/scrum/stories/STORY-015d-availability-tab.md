---
id: STORY-015d
title: Availability tab — two-grain availability (component rollup + per-signal drill-down)
type: feature
---

## Context
Spec: dossier §17, §11. Zone 7. Split-child of STORY-015; depends on STORY-015a (shell) and
**STORY-044 (Availability & topology API — HARD DEPENDENCY, not schedulable before it)**.
Re-scoped 2026-07-02 after PO clarification: a component can have MULTIPLE signals, and the tab
must show availability at BOTH grains — the component rollup (MIN across signals, counts summed —
the core's `rollup_group` semantics, "a group is only as available as its worst signal") AND each
signal individually.

## Description
Per component over a selectable time window (24h / 7d / 30d presets → tz-aware `since`/`until`):
the component-grain availability (rollup) as the headline row, expandable/drilling down to the
per-signal children (each computed with its own configured interval — supplied server-side by
STORY-044). Percentages are the headline (mono, consistent precision); completeness% and the
verdict counts give auditability; a simple tokens-styled horizontal bar per row gives shape
without a charting library (value always present as text — never bar-alone).

## Acceptance Criteria (field-level detail re-verified against the real STORY-044 endpoints at
planning, per the 2026-07-02 tab-AC-vs-DTO agreement)
- [ ] AC1: The tab lists components (via the STORY-044 topology enumeration) and shows the
      component-grain rollup availability per component for the selected window; each component
      expands to its per-signal children (signal name/key + availability% + completeness%).
- [ ] AC2: Window selector (at least 24h / 7d / 30d) drives refetches with tz-aware `since`/`until`;
      MSW tests assert the actual query params sent.
- [ ] AC3: Degenerate windows render honestly: a null availability/completeness (no-data window)
      shows an explicit "no data" treatment, never 0% or a crash. Tested.
- [ ] AC4: Loading/empty/error+retry states via shell primitives; per-tab pattern (page + feature
      hook via the shared `useFetch`, per-feature MSW module); bars are tokens-only and never the
      sole carrier of the value. Tested.

## Open Questions
None at this level — endpoint shapes finalize in STORY-044; this story's field-level AC are
reconciled at its own planning.

## History
- 2026-06-29: first version refined; reverted with `521764c`.
- 2026-07-02: re-refined for the Linear-guided direction (per-component + group rollup guess).
- 2026-07-02 (audit + PO clarification): re-scoped to two-grain (component rollup + per-signal
  drill-down) on the STORY-044 API; the earlier draft assumed a per-component list endpoint that
  does not exist and omitted the signal_key requirement. Estimate 3 (frontend only; backend lives
  in 044). Status: ready, blocked-by STORY-044.
