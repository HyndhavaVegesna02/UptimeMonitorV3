---
id: STORY-091
title: Chore — sprint-47 review minors (proposal-event orphan guard, blocker-fixture return-code check, create_open dedup)
type: chore
---

## Context
Filed at the sprint-47 review (2026-07-15, PO "accept with follow-up"). Three MINOR findings
surfaced by the external-mode reviewers that were deliberately NOT fixed as trivial tails because
each involves a judgment/behavior decision rather than a mechanical cleanup. None blocks; all are
low-risk hygiene.

## Description
Land the three deferred sprint-47 review MINORs.

## Acceptance Criteria
- [ ] AC1 (proposal-event orphan guard): in `backend/src/adapters/persistence/dynamo_proposal_repository.py`,
      `record_approval_event`'s event Put gains an `attribute_exists(pk)` (or equivalent) condition so
      an event recorded against a missing proposal fails rather than writing an orphan event item —
      restoring parity with the Postgres FK guard. (Currently unreachable via `ApprovalService._decide`,
      which loads + resolves first, so this is latent-divergence hygiene, not a live bug.) A test proves
      an event against a non-existent proposal id is rejected and writes nothing.
- [ ] AC2 (blocker-fixture return-code check): in `backend/tests/test_dev_db_cli.py`, the autouse
      `run_with_blocker` fixture asserts its blocker container actually started (checks the docker
      return code) rather than ignoring it — so the collision-proof claim cannot silently pass when the
      blocker never came up. Teardown stays leak-free (post-yield finalizer). Alternatively, if the
      blocker is judged purely decorative, remove it and rely on the dynamic-name/port design — record
      the decision either way.
- [ ] AC3 (create_open dedup): the near-identical `meta_item` / `slot_item` field-copy blocks in
      `create_open` are factored through a small shared helper (from_status/reason/resolved_at optional-
      attr wiring), with no behavior change.
- [ ] AC4 (gates): full DoD gate green; import-linter contracts pass; wiki blast radius resolved
      (sweep decides).

## Open Questions
<!-- none — AC2 offers guard-or-remove; implementer records the choice -->

## History
- 2026-07-15: filed at sprint-47 review from the three deferred quality-review MINORs (STORY-080 blocker
  fixture, STORY-085 orphan-event guard + create_open dedup). Draft — needs estimate at refinement.
