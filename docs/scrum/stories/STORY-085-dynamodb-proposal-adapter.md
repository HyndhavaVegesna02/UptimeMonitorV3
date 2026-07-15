---
id: STORY-085
title: DynamoDB proposal adapter — open-slot uniqueness transaction, counter IDs, approval events
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). This adapter carries the human-approval
gate's concurrency invariant. Postgres semantics being ported
(from `proposal_repository.py`):
- `create_open`: partial unique index (`WHERE state='open'`) via
  `ON CONFLICT DO NOTHING` — at most one OPEN proposal per component; conflict returns
  None (the `DecideService` NOOP degrade path, decide.py).
- `resolve`: `UPDATE ... WHERE id=:id AND state='open'`; rowcount≠1 →
  `ProposalNotOpenError` (covers both not-found and concurrently-resolved).
- IDs: BIGINT autoincrement — ported as an atomic `COUNTER`/`proposal` item
  (`UpdateItem ADD seq 1`) so the domain field `StatusProposal.id: int | None` (assigned
  an int on create; `DecideService` guards with `assert opened.id is not None`) stays
  untouched (PO-accepted 2026-07-14).

Approved item shapes: `PROPOSAL#<id>`/`META` (sparse `gsi1pk=PROPOSAL_OPEN` while
open); slot item `COMPONENT#<cid>`/`OPEN_PROPOSAL` with a denormalized copy of the open
proposal (safe: open proposals are immutable until resolved; the slot dies at
resolution); events `PROPOSAL#<id>`/`EVENT#<occurred_at>#<action>`.
`record_approval_event` additionally denormalizes `approved_actor` onto the proposal
META when action=approved — consumed by STORY-086's publications author derivation.

## Description
Implement `DynamoProposalRepository` satisfying `ProposalRepository`, proven against
`dynamo_local`.

## Acceptance Criteria
- [ ] AC1 (one open per component): `create_open` uses one TransactWriteItems (META put
      + slot put, both `attribute_not_exists`); a second create for the same component
      while one is open returns None with nothing written; a create for a different
      component succeeds.
- [ ] AC2 (counter IDs): assigned ids are ints, strictly increasing, unique across
      concurrent-style repeated creates; the returned `StatusProposal` carries its id.
- [ ] AC3 (resolve guard): `resolve` on an open proposal transitions state, sets
      reason/resolved_at, removes the sparse GSI attributes, and deletes the slot item
      atomically; `resolve` on a missing id or an already-terminal proposal raises
      `ProposalNotOpenError` and mutates nothing.
- [ ] AC4 (reads): `get_open` (strongly consistent slot read) and `get` return
      field-faithful `StatusProposal`s or None; `list_open` returns exactly the open
      set via the sparse GSI.
- [ ] AC5 (approval events): `record_approval_event` persists the event item and, when
      action=approved, sets `approved_actor` on the META; a full
      decide→approve lifecycle exercised through the real `DecideService` +
      `ApprovalService` against this adapter behaves identically to the Postgres run
      (PROPOSED → APPROVED, publish ordering commit-first).
- [ ] AC6 (boundaries + gates): import-linter contracts pass; six backend gates green;
      not yet wired into composition.

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 5 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
