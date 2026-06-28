---
id: STORY-037
title: Publications feature module — record Statuspage publish history for the Publications tab
type: feature
---

## Context
Spec: dossier §9 (modularity model) + §12/T1.1 (commit-first, best-effort publish). Surfaced by
Sprint 13 planning of STORY-014b: the Publications tab has NO backing state. The Statuspage publish
adapter (STORY-013, `adapters/outbound/statuspage`) publishes status changes but nothing RECORDS the
publication outcomes; there is no publications table or repository. Before a Publications read
endpoint can exist, publish history must be persisted.

## Description
A stateful **feature module** (dossier §9): owns a `publications` table FK'd into the spine
(`components` and/or `status_proposals`), recording each publish attempt (when, what change, target,
outcome/error). Written on the best-effort publish path (T1.1: after the DB commit; a publish
failure is logged AND recorded, never raised). Feeds the future Publications read endpoint.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: a publications table + Alembic migration; inward FK into the spine; FK-direction green.
- [ ] AC2: a domain type + repository port + Postgres adapter + fake (record/list), empty/edge tests.
- [ ] AC3: the publish path records each attempt (success AND failure) without breaking the
      best-effort contract (a failed publish is recorded, not raised — T1.1).
- [ ] AC4: full SIX-command DoD gate green; blast radius resolved.

## Open Questions
- Record only successful publishes, or attempts incl. failures (recommended: attempts)?
- Where the recording is wired (the composition publish helper) vs the adapter — keep core pure.
- Estimate at refinement (likely 5).

## History
- 2026-06-28: created from Sprint 13 planning (STORY-014b found the Publications tab has no backing
  state). Status: draft.
