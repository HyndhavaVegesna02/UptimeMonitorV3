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

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Severity-ordered direction: proposed worse than current → a degradation proposal (human
      gate); better → a recovery (auto-publish); same → nothing. Unit-tested with fixtures.
- [ ] AC2: Open-proposal reconciliation behaves per §10/§12 (e.g. a new proposal supersedes/obsoletes
      a stale open one; the partial-unique "one open proposal per component" invariant is honored).
- [ ] AC3: Pure and provider-blind — no vendor/HTTP/SQL imports; `lint-imports` green; tests use
      in-memory canonical fixtures; proposal domain types + persistence are consumed through a port.

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
