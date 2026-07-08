---
id: STORY-068
title: Defect — useAvailability.test.tsx false-reds under npm test file-parallelism
type: defect
---

## Context
Found at sprint-38 STORY-061 spec review (2026-07-08). On a CPU-contended parallel `npm test`
run, `frontend/src/features/availability/useAvailability.test.tsx` produced 18 uncaught
exceptions; a serialized / uncontended re-run is fully green (355/355). This is the same CLASS
of flaky-gate as the now-fixed STORY-054 (CheckHistoryPage) — a non-deterministic gate signal,
which the 2026-07-06 working agreement says must never be left standing.

`useAvailability` fans out `getComponentAvailability` per component plus a per-component segment
`getHistory` (STORY-058); the "uncaught exceptions" (vs a plain timeout) suggest an unhandled
promise rejection or a state-update-after-unmount leaking under contention, not merely a slow
render. That must be diagnosed before it is dismissed as contention.

## Description (to refine)
Diagnose whether the failures are (a) a real unhandled-rejection / act()-warning / unmounted-set
leak in the hook or its test, or (b) a pure timeout under contention. Fix accordingly: proper
async cleanup / awaited settle / cancellation guard in the test (and hook if the leak is real),
so `npm test` is deterministic under file-parallelism.

## Acceptance Criteria (to refine)
- [ ] Reproduce the false-red (or characterize it) and identify the root cause.
- [ ] `npm test` (default parallelism) passes deterministically across repeated runs incl. under load.
- [ ] If a real hook-level unhandled rejection exists, it is fixed with a regression test.

## Open Questions
- Is it an unhandled rejection on the segment-fetch degradation path, or a contention timeout?

## History
- 2026-07-08: filed from sprint-38 STORY-061 spec review. Status: draft (needs refinement + estimate).
