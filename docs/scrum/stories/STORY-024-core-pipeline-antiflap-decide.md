---
id: STORY-024
title: Core pipeline stage 4 — decide
type: feature
---

## Context
Spec: dossier §10 (stage 4, decide) + §12 (proposal lifecycle). Zone 4. The final pipeline stage,
split twice: from STORY-010 (the original four-stage 8), then again at sprint-8 refinement —
**anti-flap (stage 3) shipped as STORY-028** with injected thresholds. This story is **decide**
alone, and it is the one genuinely blocked on the **proposal lifecycle**: it emits proposals, reads
the component's current published status, and reconciles open proposals — all of which need the
proposal domain types + persistence that STORY-012 (Zone 5) owns. Depends on STORY-028 (anti-flap's
proposed status is decide's input) and STORY-012 (proposals).

## Description
In `core/services/` (the pipeline module): **decide** compares the proposed status (from anti-flap)
to the component's current published status: same → nothing; worse → a degradation **proposal**
(the human-approval gate); better → a **recovery** (auto-publishes). Also reconciles open proposals
and (later) carries the per-component skew annotation (STORY-026).

## Acceptance Criteria (refined — PO-approved 2026-06-27, sprint-10 planning)
- [ ] AC1: Severity-ordered direction vs the component's CURRENT PUBLISHED status (dossier §10): proposed
      worse than current → a degradation `create_open` proposal (the human gate), NO publish; better than
      current → an auto-published recovery via `StatusPublisherPort.publish`; same → nothing. Unit-tested
      with in-memory fakes. Severity rank: `operational < degraded < partial_outage < major_outage`.
- [ ] AC2: Open-proposal reconciliation per §12, comparing the freshly computed status to the open
      proposal: worse than the open proposal (and differing) → `resolve(SUPERSEDED)` the lesser + a new
      `create_open` for the worst (the human always sees the current worst); recovered (computed no longer
      a degradation while a pending degradation is open) → `resolve(OBSOLETED)`, **nothing published**
      (§12: the customer was never shown the outage); same as the open proposal → leave it. The
      partial-unique "one open proposal per component" invariant is honored throughout. Repo writes are
      committed BEFORE the best-effort publish (commit-first; a publish failure never loses the decision).
- [ ] AC3: Pure and provider-blind — `decide` lives in `core/services/decide.py`, imports only
      `src.core.*` (no vendor/HTTP/SQL); `lint-imports` green; a core SERVICE with injected ports
      (mirrors `IngestService`); proposals consumed through `ProposalRepository`, recovery published
      through `StatusPublisherPort`; tests use the existing `FakeProposalRepository` /
      `RecordingStatusPublisher` (no DB).

## Resolved Questions (sprint-10 refinement, 2026-06-27)
- **"Current published status" read seam → RESOLVED:** it is `components.status` (the single
  current-status column; `publications` is the append-only audit log, not the read source). `decide`
  does NOT get a new read port this sprint — `current_status: ComponentStatus` is an **injected
  parameter** (precedent: `collapse`'s `under_maintenance`, `anti_flap`'s `thresholds`). The
  composition layer / first end-to-end thread (STORY-016) reads `components.status` and supplies it.
- **Updating `components.status` + writing a `publications` row are OUT OF SCOPE** (no port for them
  here) — that persistence is STORY-016's end-to-end wiring. `decide`'s publish responsibility is
  exactly `StatusPublisherPort.publish(StatusChange(...))`.
- Full integrated §10+§12 algorithm + edge/error behavior: see
  `docs/scrum/sprints/2026-06-27-sprint-10/plan.md` (STORY-024 section) — the build contract.

## Scope note (sprint-9 refinement)
This story now ALSO owns the **reconciliation rule** (dossier §12: worse computed → supersede the
lesser open proposal + create the new worst; recovered → obsolete the open degradation, publish
nothing; same → leave), which was split out of STORY-012 at sprint-9 refinement. It CONSUMES the
substrate STORY-012 builds: the `StatusProposal`/`ProposalState` domain types and the
`ProposalRepository` port (`create_open`/`get_open`/`resolve`). The recovery "auto-publish" emits a
canonical `StatusChange` to the `StatusPublisherPort` (STORY-013), committed-then-best-effort.

## Open Questions
- "Current published status" read — decide compares its proposed status against the component's
  current PUBLISHED status. Confirm the seam at refinement: a read port over the `publications` /
  `components.status`? (STORY-012 + STORY-013 land the proposal + publish halves first; resolve this
  read seam when STORY-024 is planned.) This story stays draft until then.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §10. Status: draft.
- 2026-06-25: split from STORY-010 (the four-stage 8) into stages 3–4.
- 2026-06-25 (sprint-8 refinement): split AGAIN — anti-flap (stage 3) shipped as STORY-028 with
  injected thresholds; this story is now **decide** (stage 4) ALONE, re-estimated 5 → 3 (less work
  without anti-flap, but still blocked on the proposal seam). Status: draft — depends on STORY-012
  (proposals); resolve the seam at refinement. Proposed estimate: 3.
- 2026-06-27 (sprint-10 refinement + planning): deps all Done (STORY-028/012/013). Open question
  RESOLVED — current published status = `components.status`, injected as a `current_status` parameter;
  read wiring deferred to STORY-016. AC finalized against dossier §10 + §12 (two comparisons: vs
  published drives the publish, vs the open proposal drives supersede/obsolete). Estimate held at 3.
  Status: ready → committed to Sprint 10 (the headline). Build contract: the sprint-10 plan.md.
