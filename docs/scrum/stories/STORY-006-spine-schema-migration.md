---
id: STORY-006
title: Spine schema migration
type: feature
---

## Context
Spec: dossier §9 (Neon data model — the stable spine), with the partial-unique
proposal constraint reaching into §11. Zone 2. This is the load-bearing foundation:
every later zone foreign-keys *inward* to these tables, never the reverse, and the
FK-direction CI check (`scripts/check_fk_direction.py`) already hard-codes all eleven
of them in its `SPINE` allowlist. High blast radius — it earns the full review pipeline.

Refined 2026-06-24: build the **full eleven-table spine** in one reversible migration
(PO decision — keeps the spine coherent and leaves Zone 5 with no stranded schema story).
Per-app behavioral config is a **JSONB `config` column on `apps`** (PO decision; §9 offered
either a column or a thin `app_config` table — the config is a resolved, seeded, opaque
bag the core reads whole, which is what JSONB is for).

## Description
One Alembic migration (on top of the empty `eda70ac11454` baseline) creating the three
table groups of the spine. The team specifies exact columns building to §9 and the
canonical domain types (`SignalObservation`, `StatusChange`); the headline structures and
constraints below are fixed AC.

- **topology** (seeded from Git config at boot; idempotent upsert later):
  `apps`, `signals`, `components`. `apps` carries the JSONB `config` column.
- **signals** (runtime, append-only): `observations`, `problem_signals`, `watermarks`,
  `rejected_observations`. `observations` mirrors the canonical `SignalObservation`
  fields (`signal_key`, `observed_at`, `health`, `source_event_id`, `source`, `location`,
  `latency_ms`, `raw_ref`); `watermarks` is keyed by `signal_key` (matches the
  `WatermarkRepository` port: `get(signal_key)` / `advance(signal_key, to)`).
- **workflow** (runtime, V2-proven shapes): `status_proposals`, `approval_events`,
  `publications`, `maintenance_windows`.

`timestamptz` everywhere; `JSONB` for `apps.config`, `observations.source`, and the
`rejected_observations` payload. Strong FKs, every one with an **explicit `ON DELETE`**:
runtime/workflow tables FK *into* the spine with `ON DELETE RESTRICT` (seeded topology and
runtime truth are never silently cascaded away). No spine→feature FK (none can exist yet —
every table here is spine).

## Acceptance Criteria
- [ ] AC1: `alembic upgrade head` applies the migration to a fresh DB, exit 0, and all
      eleven spine tables exist: `apps`, `signals`, `components`, `observations`,
      `problem_signals`, `watermarks`, `rejected_observations`, `status_proposals`,
      `approval_events`, `publications`, `maintenance_windows`.
- [ ] AC2: `scripts/check_fk_direction.py` exits 0 against the migrated DB (every FK points
      within the spine; zero spine→feature violations).
- [ ] AC3: The three required indexes exist and are verifiable in `information_schema`:
      a UNIQUE constraint/index on `observations(source_event_id)`; a composite index on
      `observations(signal_key, observed_at)`; and a **partial UNIQUE index on
      `status_proposals(component_id)` filtered to active proposals** — enforcing at most
      one active proposal per component (§9 → §11).
- [ ] AC4: Every timestamp column is `timestamptz` (no `timestamp`/text-date columns); the
      JSONB columns `apps.config`, `observations.source`, and the `rejected_observations`
      payload are `jsonb`. `apps.config` is `NOT NULL`.
- [ ] AC5: The migration round-trips: `alembic upgrade head` → `alembic downgrade base` →
      `alembic upgrade head` each exit 0 (downgrade drops every spine object cleanly).
- [ ] AC6: Every FK declares an explicit `ON DELETE` behavior (`RESTRICT` for references
      into seeded topology), verifiable in `information_schema.referential_constraints`;
      no FK relies on the default.

## Open Questions
_(none — ready)_

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §9. Status: draft.
- 2026-06-24: refined with PO. Decisions: (1) full eleven-table spine in one migration,
  not split; (2) per-app config = JSONB `config` column on `apps`, not a separate table;
  (3) explicit `ON DELETE RESTRICT` on FKs into topology. AC made testable against
  `information_schema`. Estimate held at 5 (high blast radius → full review pipeline).
  Status: ready. Planned into Sprint 2.
- 2026-06-24: implemented (migration `3a8254bcfe59`, commits `54eb5c5`, `cc54e13`).
  Spec review PASS (all 6 AC MET, verified against live Postgres); quality review APPROVE
  (zero critical/major). DoD gate green (alembic head, pytest 77, lint-imports 3 kept,
  FK-direction 10 checked/0 violations). Board: done. Awaiting PO acceptance at review.
  Implementer decisions within AC: health/status/state stored as `text` + CHECK mirroring
  the closed Python enums (not Postgres ENUM, so the enums stay the single source of truth);
  `rejected_observations.signal_key` has NO FK (quarantine must not be rejectable by a
  missing-FK error); `approval_events`/`publications` → `status_proposals` use explicit
  `ON DELETE CASCADE` (child audit/publish rows have no meaning without their proposal).
  Quality-review MINOR notes (non-blocking, no change required): (1) `downgrade()` drops
  `uq_observations_source_event_id` explicitly before its table — harmless/symmetric;
  (2) the composite-index column-order test uses a substring-position heuristic on the
  index def rather than parsing `pg_index` order — acceptable for a presence test.
