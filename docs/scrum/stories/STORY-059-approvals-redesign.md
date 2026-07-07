---
id: STORY-059
title: Approvals redesign — card layout with severity stripe, from→to pills, confirm flow, "Queue clear" empty state (adapt to real data)
type: feature
---

## Context
Wave 2 (parallel). Depends on 055 + 056. Rebuilds `pages/ApprovalsPage.tsx` + `features/approvals/*`
to the mock's card layout (plan.md §"Approvals"). Preserves the decision state machine + 409/404
handling exactly. Adapt to real data — no fakes.

## Acceptance Criteria
- [ ] AC1: Card layout with a severity accent stripe — severity DERIVED from `to_status`
      (major_outage→major, partial_outage→partial, degraded→degraded, else unknown), NOT a fake
      field; from→to status pills (→ arrow; "New" when `from_status` is null); real `proposed_at`.
- [ ] AC2: Approve/Reject preserve the idle→confirming→submitting→failed state machine, the inline
      reject confirm, and the 409/404 notice banner (`role="status"`); `postDecision` + `getActor`
      unchanged.
- [ ] AC3: "Queue clear" empty state when no pending proposals. Fields the API does not expose
      (reason/source/detected-ago/checks/triggering-signals) are OMITTED, not faked → STORY-063.
- [ ] AC4: Frontend three-gate DoD green; empty backend diff; wiki sweep resolved.

## Open Questions
None — proposal enrichment deferred to STORY-063.

## History
- 2026-07-07: drafted + refined at sprint-38 planning. Status: ready. PO-approved.
