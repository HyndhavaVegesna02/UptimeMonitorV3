---
id: STORY-006
title: Spine schema migration
type: feature
---

## Context
Spec: dossier §9 (Neon data model — the stable spine). Zone 2. The three table groups
and the integrity constraints the whole design relies on.

## Description
Alembic migration creating the spine: **topology** (`apps`, `signals`, `components`),
**signals** (`observations`, `problem_signals`, `watermarks`, `rejected_observations`),
**workflow** (`status_proposals`, `approval_events`, `publications`,
`maintenance_windows`). Use `timestamptz` everywhere, `JSONB` for `source`/payloads,
`UNIQUE(source_event_id)`, a composite index on `(signal_key, observed_at)`, and a
**partial unique index** enforcing one active proposal per component. Strong FKs with
explicit `ON DELETE` behavior; feature tables FK INTO the spine, never the reverse.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: `alembic upgrade head` applies the migration to a fresh DB, exit 0.
- [ ] AC2: `scripts/check_fk_direction.py` passes (no spine→feature FK).
- [ ] AC3: The required indexes exist: `UNIQUE(source_event_id)`, composite
      `(signal_key, observed_at)`, and the partial unique index for one active proposal
      per component.
- [ ] AC4: `timestamptz` and `JSONB` used per §9; migration is reversible
      (`downgrade` → `upgrade` round-trips).

## Open Questions
- Confirm exact columns per table and `ON DELETE` choices at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §9. Status: draft — refine before its sprint.
