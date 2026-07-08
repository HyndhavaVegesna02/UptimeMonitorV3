---
id: STORY-069
title: Chore — sprint-38 redesign consolidation minors
type: chore
---

## Context
Accumulated NON-blocking MINOR findings from the sprint-38 Operator Dashboard redesign Opus
reviews. None blocked their stories (all APPROVED); grouped here for a single cleanup pass. The
duplication items exist because Wave-2 pages were built in isolated worktrees (couldn't share a
not-yet-created module), a deliberate parallelism trade-off now worth consolidating.

## Description / checklist (to refine)
- **Extract `frontend/src/features/history/uptimeSegments.ts`** (`buildUptimeSegments` +
  `MAX_UPTIME_SEGMENTS`) and consume it from BOTH `dashboard/useComponentUptime.ts` and
  `availability/segments.ts` — they are currently byte-identical copies (058 + 057 reviews).
- **Fix stale docstrings** in `dashboard/useTopology.ts` and `dashboard/useComponentSignals.ts`
  that still reference the removed `useSignalOptions.ts` / `useHistory.ts` (060 review).
- **Consolidate the two `getTopology` wrappers** (`dashboard/useTopology.ts`) if still duplicated
  after the above (057 review).
- **SummaryCard tone vocab**: align `'ok'` with `HealthStatus 'up'` (or document the divergence)
  so consumers don't hand-map (055 review).
- **Tokenize magic numbers**: `SummaryCard` big-number 24px → a `--fs-stat` token; `ApprovalCard`
  chip 10.5px; Approvals badge radius/border; `.maintenance-window__title` font-weight (055/059/061).
- **A11y enhancements** (non-regressions): `aria-controls` on the Dashboard/Availability expanders;
  `aria-invalid`/`aria-describedby` on Maintenance 422 fields; SR-per-segment summary on `UptimeBar`.

## Acceptance Criteria (to refine)
- [ ] The duplications are removed (single shared module) with tests green.
- [ ] Stale docstrings corrected; token/a11y nits applied.
- [ ] Frontend three-gate DoD green; empty backend diff.

## Open Questions
- Split the a11y enhancements into their own story, or fold in here? (PO/refinement call.)

## History
- 2026-07-08: filed from sprint-38 review MINORs. Status: draft (needs refinement + estimate).
