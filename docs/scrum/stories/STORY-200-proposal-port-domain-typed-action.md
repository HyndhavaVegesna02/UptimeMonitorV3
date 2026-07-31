---
id: STORY-200
title: Give ProposalRepository.record_approval_event a domain-typed action parameter
type: defect
points: 2
status: draft
refined: 2026-07-31
---

## Context

Filed from the sprint-66 audit's quality-review fix round (STORY-195,
`docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2b/§3). An independent re-audit
found that `STORY-195`'s original pass adjudicated a hardcoded-literal comparison in
`DynamoProposalRepository.record_approval_event` (`GAP-1`, filed as `STORY-198`, already landed) as an
unscored "catalogue gap" while separately verdicting `core/ports/proposal_repository.py` `CLEAN` —
having quoted the very port line (`action: str`) that is the ROOT CAUSE, without recognizing it as
one. This is now catalogued as `ZR-6` in `docs/scrum/wiki/zone-rules.md`.

## Description

`backend/src/core/ports/proposal_repository.py:45` (`action: str`, in `record_approval_event`'s
abstract signature) stands in for `ProposalState` even though `ProposalState` is imported in the SAME
file (`backend/src/core/ports/proposal_repository.py:6`) and used correctly, as the domain type, by
the sibling method four lines above: `backend/src/core/ports/proposal_repository.py:32`
(`to_state: ProposalState`, in `resolve`'s signature). The adapter implementing this port,
`backend/src/adapters/persistence/dynamo_proposal_repository.py:286`
(`if action == "approved":`), then compares the resulting bare string against a hardcoded literal
rather than an enum member — the exact shape a correctly-typed port signature would make structurally
awkward to get wrong.

**The real design choice this story must make (not mechanical):** `action`'s legal set today is a
2-member subset of `ProposalState`'s 5 members — only `APPROVED`/`REJECTED` are ever passed
(`backend/src/core/services/approval.py:60-70` calls `_decide(..., to_state=ProposalState.APPROVED,
...)`, `:72-88` calls `_decide(..., to_state=ProposalState.REJECTED, ...)`, and `_decide` derives
`action=to_state.value` at `backend/src/core/services/approval.py:128`). The full `ProposalState` enum
also carries `OPEN`, `SUPERSEDED`, `OBSOLETED`, none of which is ever a valid `action`. Refinement must
choose between:

- (a) widen the port to accept `ProposalState` directly, accepting that 3 of 5 members are
  semantically invalid `action`s, or
- (b) introduce a narrower, purpose-built type (e.g. a 2-member `ApprovalAction` enum) expressing
  exactly the legal set.

**Overlap with `STORY-198` (already landed, not reopened by this story):** `STORY-198` fixes the
ADAPTER's comparison (`dynamo_proposal_repository.py:286`) to compare against
`ProposalState.APPROVED.value` instead of the literal `"approved"`, but leaves `action`'s TYPE at the
port as `str`. If this story lands after `STORY-198` and changes the port to accept a domain type
directly, `STORY-198`'s own `.value`-based comparison may become unnecessary or need updating again —
this reconciliation must happen at this story's refinement, not be assumed away.

## Acceptance Criteria

- [ ] **AC1** — `ProposalRepository.record_approval_event`'s abstract signature no longer types
      `action` as a bare `str`; it uses a domain type expressing either the full `ProposalState` or a
      narrower purpose-built approval-action type (refinement decides which, per the Description).
- [ ] **AC2** — `DynamoProposalRepository.record_approval_event`'s implementation and every caller
      (`core/services/approval.py`'s `_decide`) are updated to match the new signature.
- [ ] **AC3** — A test demonstrates the chosen option's constraint is real and enforced: either the
      narrower type rejects an out-of-set value at construction, or (if the full-enum option is
      chosen) a test/comment documents that the 3 semantically-invalid `ProposalState` members are
      never passed by any caller — whichever option refinement picks must leave an explicit, testable
      trace of the decision, not silence.
- [ ] **AC4** — Existing `DynamoProposalRepository`/`ApprovalService` contract tests continue to pass.

## Open Questions

- (a) vs (b) above is a genuine refinement decision, not resolved by this filing.

## History

- 2026-07-31: filed from STORY-195's quality-review fix round finding (`ZR-6`,
  `docs/scrum/sprints/2026-07-31-sprint-66/audit-core-adapters.md` §2b/§3/§6).
