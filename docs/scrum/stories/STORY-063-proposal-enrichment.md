---
id: STORY-063
title: Proposal enrichment — severity / reason / source / triggering-signals on ProposalDTO
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The *Operator Dashboard* mock's
Approvals cards show a severity tag, a human reason, a source, "detected X ago", a check count, and
triggering-signal chips. The current `ProposalDTO` (`api/v1/approvals/models.py`) is
`{id, component_id, from_status?, to_status, state, proposed_at}` — none of that. STORY-059 adapts
by deriving severity from `to_status` and omitting the rest; this story adds the real data.

## Description (to refine)
Enrich the proposal read model + `ProposalDTO` with the fields the approvals UI wants, sourced from
the real proposal/anti-flap/decision pipeline (severity, the triggering signals + their observations,
detection time, check counts, a reason string). Backend story — five-file API conventions, DTO/domain
distinction, tz-aware datetimes. Then a small frontend follow-up surfaces them in the 059 cards.

## Acceptance Criteria (to refine)
- [ ] Determine which fields are genuinely derivable from persisted state vs. need new capture.
- [ ] Extend `ProposalDTO` (+ producing `service.py`) with the derivable fields; tests.
- [ ] Frontend: render the new fields in the Approvals cards (chips, reason, detected-ago).

## Open Questions
- Which fields exist in the pipeline today vs. require new persistence? (Probe before estimating.)

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
- 2026-07-12: probe findings recorded (pilot sprint 44 refinement pass; stays DRAFT — deferred):
  `StatusProposal.reason` exists but is populated only at resolve (`decide.py::DecideService`
  resolve paths), never at creation; severity / triggering-signals / check-counts need NEW
  capture — the observation batch is in scope in `orchestrate.py::orchestrate_signal` but only
  `component_id/proposed_status/current_status/now` reach `decide`. So this is producer-side
  design + persistence (likely 5 pts): decide-time capture of reason/severity/triggering signal
  ids, schema addition, then DTO threading. Open design questions for next refinement: severity
  semantics (derived from to_status transition vs computed), triggering signals as list vs
  representative id, and whether reason becomes a creation-time field or a separate audit field.
