---
id: STORY-007
title: Repository adapters behind the ports
type: feature
---

## Context
Spec: dossier §6 (repository ports) + §9 (schema). Zone 2. Neon/Postgres-backed
implementations of the two persistence ports that exist after STORY-005:
`ObservationRepository` (`save_new`) and `WatermarkRepository` (`get` / `advance`). They
sit in `adapters/persistence/` and run against the spine tables created by STORY-006. All
SQL stays behind the repository layer — the existing `core-independence` import contract
already forbids `sqlalchemy` inside `src.core`, so a leak is a build failure, not a review
note.

Refined 2026-06-24: scope is exactly those two repositories (no others have ports yet —
nothing is deferred). Depends on STORY-006; planned for Sprint 3 so the spine is
PO-accepted before adapter code and integration tests are written against it.

## Description
Implement two concrete adapters in `adapters/persistence/` (SQLAlchemy 2 / psycopg 3):

- `ObservationRepository.save_new(batch)` → `INSERT … ON CONFLICT (source_event_id) DO
  NOTHING`, returning the count of rows **newly** inserted (so the core can report
  accepted-vs-deduped without SQL leaking upward).
- `WatermarkRepository.get(signal_key)` / `advance(signal_key, to)` → DB-backed cursor;
  core-owned in semantics, stored here. `to` is a tz-aware UTC `datetime` and must
  round-trip through `timestamptz` unchanged.

Integration tests run against a **throwaway Dockerized Postgres** migrated with
`alembic upgrade head` (per the working agreement: real adapters use a throwaway test DB,
never a mock of the database). No live Neon required.

## Acceptance Criteria
- [x] AC1: A concrete `ObservationRepository` and a concrete `WatermarkRepository` live in
      `adapters/persistence/`, each implementing its STORY-005 port interface (subclass /
      registered ABC), constructed with an injected SQLAlchemy engine/session.
- [x] AC2: Integration tests run against a Dockerized Postgres migrated to head and cover,
      for observations: inserting a fresh batch, reading it back, and the dedup path; for
      watermarks: `get` before any advance, `get` after `advance`, and re-`advance`.
- [x] AC3: `save_new` is idempotent: re-inserting a batch whose `source_event_id`s already
      exist inserts **0** new rows and the returned count reflects only newly-inserted rows
      (`ON CONFLICT (source_event_id) DO NOTHING`), proven by a duplicate-insert test.
- [x] AC4: `WatermarkRepository.get` returns `None` before the first `advance`, returns the
      advanced instant afterward as a tz-aware UTC `datetime`, and a later `advance` moves
      it forward — proven by tests.
- [x] AC5: No SQL appears above the repository layer; `lint-imports` stays green (the
      existing `core-independence` contract forbids `sqlalchemy` in `src.core`) and review
      confirms no raw SQL leaks above `adapters/persistence/`.
- [x] AC6: All four DoD commands exit 0 (`pytest`, `lint-imports`,
      `scripts/check_fk_direction.py`, `alembic upgrade head`).

## Open Questions
_(none — ready)_

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §6/§9. Status: draft.
- 2026-06-24: refined with PO. Scope resolved to the two existing persistence ports
  (`ObservationRepository`, `WatermarkRepository`); nothing deferred (no other ports yet).
  Confirmed the no-SQL-in-core boundary is the existing `core-independence` contract, not a
  new one. Estimate held at 3. Status: ready. Sequenced for Sprint 3 (depends on STORY-006).
- 2026-06-25: implemented — `PostgresObservationRepository`/`PostgresWatermarkRepository` in
  `adapters/persistence/`, injected SQLAlchemy `Engine`. `save_new` uses
  `insert(...).on_conflict_do_nothing(index_elements=["source_event_id"]).returning(...)` and
  counts `len(fetchall())` (RETURNING yields only newly-inserted rows → exact accepted-vs-deduped
  delta); `advance` is a single `on_conflict_do_update` upsert; `get` forces tz-aware UTC via
  `.astimezone(timezone.utc)`. Tests seed parent `apps`+`signals` (raw psycopg arrangement) for
  the FK and use the `migrated_db` fixture from STORY-019. Spec review PASS (6/6 AC), quality
  review APPROVE (0 critical/major). DoD green @ f11a7be (alembic, pytest 89, lint 3 kept, FK
  10/0). Board: done. Quality-review MINOR notes (non-blocking, no change required): (1) `advance`
  doesn't refresh `watermarks.updated_at` on re-advance — audit metadata only, nothing reads it;
  (2) repo imports sit inside test functions (TDD residue), could be hoisted.
