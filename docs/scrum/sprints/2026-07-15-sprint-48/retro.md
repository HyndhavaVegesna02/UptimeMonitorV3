# Sprint 48 — Retrospective

**Delivered:** 7/7 points, both stories accepted, merged to main (`798804a`). Mode: external
(3rd consecutive). No blocks, no effort-cap trips, no hotfixes.

## What went well
- **Estimates dead-on.** 086 (5) and 091 (2) both accurate.
- **The external-mode floor did its job.** The independent nine-command gate confirmed the
  self-reported 622-pass; the review pipeline caught a real defect the delivery's own tests
  missed; the reality gate ran the hardest AC paths live vs DynamoDB-Local.
- **A good divergence was recognized as good.** The AC1 orphan-guard deviation from the
  plan's literal instruction was correctly identified (by both spec + quality reviewers) as
  a *correction*, not a regression — not blindly rejected for being off-plan.

## What dragged — two incidents, two amendments

### Incident A → Amendment A (spec-review checklist)
STORY-091 AC2 said "teardown stays leak-free." The delivered test exercised only the happy
path; the leak lived on the FAILURE path (blocker-start fails → assert before `yield` →
`docker rm -f` cleanup skipped). Quality review approved (happy path clean); spec review
caught it by reproducing the negative path. Recurring external-delivery shape: self-review
tests the path it built, not the negative one an AC clause describes.

**Amendment (PO-approved 2026-07-15), rung = spec-review checklist item:** for any AC clause
naming a failure/negative/cleanup behavior ("leak-free", "rejects X", "does not write",
"raises on missing"), the driving test must exercise the FAILURE path — a happy-path-only
test for a negative clause is a FAIL finding. Landed in `.scrum/checklists/spec-review.md`.

### Incident B → Amendment B (plan-verification checklist)
The plan (LOCK_READY) told the external agent to add `attribute_exists(pk)` to the event Put
in `record_approval_event`. That is infeasible — on a create the event item's own key does
not exist yet, so the condition fails every happy-path write. The agent silently corrected
it to a ConditionCheck-on-META. The plan-verifier passed the check because it verified "is a
guard specified?" not "would this exact vendor expression actually work?". We got lucky with
a careful agent; a literal one ships a broken guard.

**Amendment (PO-approved 2026-07-15), rung = plan-verification checklist item (external
section):** any concrete vendor mechanism the plan prescribes literally (a specific condition
expression, key shape, transaction item, API-call form) is checked for FEASIBILITY against
the vendor's actual semantics, not just presence — an infeasible literal instruction is a
GAP even when the intent is right. Landed in `.scrum/checklists/plan-verification.md`.

## Minor / carried
- STORY-086 quality minors (non-blocking): `seed_dynamo.py` docstring "full overwrite"→
  "upsert"; maintenance `ExpressionAttributeNames` aliasing consistency. → next planning /
  a review-minors chore.
- Wiki: the delivery set `persistence-adapters.md` `verified_sha` to the lock commit
  (predating its own diff), tripping the staleness sweep; fixed at the compile pass (bumped
  to final HEAD). Mechanical, low-cost — not worth a rule yet; watch for recurrence.
- Pre-existing wiki staleness: `dev-setup-and-dod.md` stale since sprint-47's DoD amendment
  (not this sprint's diff) — rehabilitate when its refs next enter a sprint.

## Process metrics
- Velocity: 7/7 (committed = accepted). Recent: 45→6, 46→8, 47→15, 48→7.
- Reviewer rejection loops: 1 (STORY-091 AC2, fixed as an orchestrator tail per edge-case #13).
- Plan-verifier: 11/11 technical PASS at planning, 3 hygiene GAPS fixed pre-lock.

## Next
Sprint cycle closed. Natural next at planning: **STORY-087** (composition cutover to DynamoDB
— now unblocked, 083–086 all accepted; retires Postgres + flips the DoD amendment), then
STORY-088 (CloudFormation). Skill → v2.1.4 (2 checklist amendments).
