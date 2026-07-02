---
id: STORY-045
title: Defect — approved proposals go nowhere: no publish on approval, and components.status is never written back
type: defect
---

## Context / how it surfaced
Found by the 2026-07-02 full-codebase audit (chairman-verified). Two connected gaps that together
break the product's core loop (dossier §12, §17 — "a degradation appears as a proposal, a human
approves it, and only then does it reach the public page"; the backend "publishes the approved
status to Statuspage"):

1. **Approval is a dead end.** `core/services/approval.py::ApprovalService` is constructed with
   ONLY `proposal_repo` + `clock` — no publisher. `approve()` resolves the proposal to APPROVED and
   records the approval event, and that is ALL. Grep-verified: nothing anywhere in `backend/src`
   consumes an APPROVED proposal (no publisher call, no poller, no branch). An operator-approved
   degradation NEVER reaches Statuspage, is NEVER recorded in `publications`, and NEVER changes any
   status.
2. **`components.status` is never written after seeding.** The `ComponentRepository` port has only
   `list_components`/`get` (no status write); `PostgresComponentRepository` performs no UPDATE; the
   only persistence UPDATEs in the codebase are proposals, watermarks, and seed metadata upserts
   (`composition/seed.py:54`: components upsert "NEVER [touches] runtime status"). Yet
   `core/services/decide.py:24` documents `current_status` as injected FROM `components.status`
   ("the component's CURRENT PUBLISHED status", dossier §12).

**Compound consequence (verified):** `GET /api/v1/components` serves "operational" forever, so the
Dashboard tab can never change; decide always compares proposals against a frozen
current=operational — which ALSO makes the recovery branch (`proposed better than current`)
unreachable, since nothing is better than operational. As built, the live system can only open
proposals; nothing it decides ever reaches the public page or the read model.

## Acceptance Criteria
- [ ] AC1 (approve publishes): approving an open degradation proposal publishes the approved status
      to the Statuspage publisher chain (Recording → BestEffort → Statuspage, as wired for
      recoveries in `composition/run.py`) and records a row in `publications` — proven by a test
      that approves via the service and asserts the publisher received the `StatusChange` AND the
      publication was recorded. Reject publishes nothing (tested).
- [ ] AC2 (status write-back): after an approved-degradation publish AND after a recovery publish,
      `components.status` reflects the new status — `GET /api/v1/components` returns it, and the
      next pipeline cycle's `decide` reads it as `current_status`. Tested at both trigger points.
- [ ] AC3 (port + parity): the `ComponentRepository` port gains the status-write method; the
      Postgres adapter and the in-memory fake implement it with IDENTICAL edge behavior (unknown
      component id → same named domain error in both), proven by the same contract test against
      both (2026-06-26 fake/adapter-parity agreement).
- [ ] AC4 (ordering per §T1.1 commit-first): DB writes (proposal resolution, publication record,
      status write-back) are durably committed such that a Statuspage outage cannot lose the
      decision; the publish remains best-effort where the dossier says so. The exact
      write-back-vs-publish-success ordering is specified in the sprint plan (edge behavior named
      explicitly per the 2026-06-26 plan-edge-behavior agreement) — not improvised.
- [ ] AC5 (recovery reachability regression): with a component written back to a degraded status, a
      subsequent UP verdict produces a recovery publish (the previously-unreachable decide branch)
      — an end-to-end orchestration test drives degrade→approve→recover and asserts the full chain.
- [ ] AC6: all existing gates stay green; the wiki articles whose Facts this changes
      (`statuspage-publish`, `core-pipeline-and-availability`, `api-five-file-convention` as
      applicable) are updated in the same story (blast radius).

## Open Questions
None blocking refinement; the AC4 ordering decision is made at sprint planning (named edge
behavior in plan.md).

## History
- 2026-07-02: filed from the full-codebase audit (H1 + the approval-publish gap found while
  verifying it). The approve-side publish never had a story: STORY-013 built the publish adapter,
  STORY-016 wired it for recoveries, STORY-012/014 built the proposal lifecycle — the
  approve→publish→write-back seam fell between them. Estimate 5. Status: ready.
