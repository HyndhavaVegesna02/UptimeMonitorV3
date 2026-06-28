---
id: STORY-016
title: First end-to-end thread
type: feature
---

## Context
Spec: dossier §17 (demo path). Integration. The deliberate first DEMOABLE thread — by
design, the first visible end-to-end behavior (earlier zones demo proven layers).

**Split (Sprint 15 planning, 2026-06-28).** The orchestration *logic* (run the pipeline per cycle →
produce proposals → publish-on-approve), which is fake-testable backend, moved to **STORY-016a**
(itself blocked on the §7/§17 config layer, STORY-040). THIS story is now just the **live e2e demo**:
point the (already-built + fake-tested) orchestration at real Dynatrace + Statuspage and observe the
thread end to end. Gated on live credentials.

## Description
With STORY-016a's orchestration in place, wire one real thread LIVE: one Dynatrace monitor → pull
loop → canonical observation → pipeline → proposal → human approval → Statuspage publish. A forced
failure via the shim produces a proposal that, once approved, publishes — observed end to end against
real services.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: A forced failure (via the shim) produces a degradation proposal visible on
      the dashboard.
- [ ] AC2: Approving that proposal publishes the status change to the real Statuspage —
      observed end to end.
- [ ] AC3: The thread runs against deployed/integrated components (not just unit mocks).

## Open Questions
- Confirm which monitor/route is the headline thread and the live-credential plan at
  refinement (this is the first story needing live Dynatrace + Statuspage).

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft — refine before its sprint.
