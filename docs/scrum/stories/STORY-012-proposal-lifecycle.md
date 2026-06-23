---
id: STORY-012
title: Proposal lifecycle
type: feature
---

## Context
Spec: dossier §12 (proposal lifecycle) + T1.2. Zone 5. A proposal is valid only while it
still matches what the engine currently computes; each cycle reconciles open proposals.
Closes a real V2 bug (stale approval publishing a finished outage).

## Description
Reconciliation rule each cycle: worse computed → pending lesser proposal → `superseded`,
new active proposal created; recovered → pending degradation → `obsoleted` (audit reason,
nothing published); same → leave it. Terminal states: `superseded`, `obsoleted` (plus
published/rejected). One active proposal per component enforced by the partial unique
index; concurrent collision → `ON CONFLICT DO NOTHING` + debug log.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: A worse proposal supersedes a pending lesser one (only one active proposal
      per component remains — the current worst).
- [ ] AC2: A recovering pending degradation is obsoleted, NOT published (with an audit
      reason).
- [ ] AC3: A concurrent duplicate insert is safe (`ON CONFLICT DO NOTHING` + debug log),
      proven by a test.
- [ ] AC4: The partial unique index enforces one active proposal per component.

## Open Questions
- Confirm the exact set of "actionable" states the partial index covers at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §12. Status: draft — refine before its sprint.
