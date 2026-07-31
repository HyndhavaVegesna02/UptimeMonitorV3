---
id: STORY-198
title: Fix the hardcoded "approved" literal in DynamoProposalRepository.record_approval_event
type: defect
points: 1
status: draft
refined: 2026-07-31
---

## Context

Filed from the sprint-66 audit (STORY-195,
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md`, finding `GAP-1`). Not a `ZR-n`
catalogue violation — none of `ZR-1..ZR-5` covers intra-`backend/src/` duplication of a domain enum's
value as a literal — but a genuine, independently-worth-fixing drift risk the audit's per-file read
surfaced. `docs/scrum/wiki/zone-rules.md`'s STORY-197 pass may separately choose to adjudicate a
`ZR-6` rule generalizing this shape; this story's fix does not depend on that happening.

## Description

`DynamoProposalRepository.record_approval_event`
(`backend/src/adapters/persistence/dynamo_proposal_repository.py:286`) branches on the hardcoded
string literal `"approved"` to decide whether to denormalize an `approved_actor` attribute onto the
proposal's META item:

```python
if action == "approved":
    ...
```

`action`'s only two real values are `ProposalState.APPROVED.value` / `ProposalState.REJECTED.value`
(`core/services/approval.py:128` derives `action=to_state.value`; the port signature
`ProposalRepository.record_approval_event` at `backend/src/core/ports/proposal_repository.py:44`
types `action: str`, never the enum itself). `ProposalState` is already imported in this same file
(for the correct, enum-member comparison at line 105:
`if proposal.state == ProposalState.OPEN:`), so there is no missing-import reason for the literal at
line 286 — it is an avoidable duplication of a domain value that a rename of
`ProposalState.APPROVED`'s value would silently break, with no import-linter or type-check signal.

## Acceptance Criteria

- [ ] **AC1** — `record_approval_event`'s branch compares against `ProposalState.APPROVED.value` (or
      an equivalent enum-member comparison), never the bare string literal `"approved"`.
- [ ] **AC2** — A test pins the comparison against the ENUM, not a copy-pasted string: e.g. assert
      that calling `record_approval_event` with `action=ProposalState.APPROVED.value` denormalizes
      `approved_actor` onto the META item, and that the source line itself references
      `ProposalState.APPROVED` (a source-inspection assertion, mirroring the project's existing
      "neither root reads `os.environ` directly" style checks) rather than merely re-asserting the
      current passing behavior with the same two literal inputs (which would pass unchanged whether
      or not the fix landed).
- [ ] **AC3** — Existing `DynamoProposalRepository` contract tests continue to pass unchanged — this
      is a like-for-like literal replacement, not a behavior change for either of the two real inputs
      (`"approved"` / `"rejected"`).

## Open Questions

None.

## History

- 2026-07-31: filed from STORY-195's audit finding `GAP-1`
  (`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md`).
