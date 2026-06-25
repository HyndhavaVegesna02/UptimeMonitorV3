---
title: Persistence adapters — the repository implementations
code_refs: [backend/src/adapters/persistence/observation_repository.py, backend/src/adapters/persistence/watermark_repository.py, backend/tests/test_persistence_adapters.py]
verified_sha: 5f38fd7
verified_sprint: sprint-3
status: verified
---

## Facts (verified against code)

The concrete Postgres implementations of the core's persistence ports (STORY-007, Zone 2).
They live ONLY in `backend/src/adapters/persistence/`; all SQL stays here (the
`core-independence` contract forbids `sqlalchemy` in `src.core`). Each imports inward
(`src.core.ports`, `src.core.domain`) and never another adapter.

### Convention: injected SQLAlchemy `Engine`, never a global
- Both repositories take an `Engine` in `__init__` and store it on `self._engine`
  (`observation_repository.py:40`, `watermark_repository.py:31`). There is no module-global
  engine and no composition wiring yet — tests construct the engine from the
  `migrated_db` fixture's URL (converted to the `postgresql+psycopg://` dialect for SQLAlchemy 2).
  A real composition-root engine factory is a later story.
- Tables are declared as lightweight `sa.table(...)`/`sa.column(...)` constructs, NOT ORM
  models (`observation_repository.py:24`, `watermark_repository.py:21`) — there are no
  SQLAlchemy models in this project; the schema's source of truth is the Alembic migration
  `3a8254bcfe59` (see [[migrations-and-db]]). The `observations.source` column must be typed
  `JSONB` on the construct (`observation_repository.py:30`) or psycopg3 raises
  `cannot adapt type 'dict'`.

### `PostgresObservationRepository.save_new` — DB-level idempotency
- `INSERT … ON CONFLICT (source_event_id) DO NOTHING … RETURNING source_event_id`
  (`observation_repository.py:68-73`), run inside `engine.begin()` (one commit).
- The **newly-inserted count** is `len(result.fetchall())` (`:77`): a row skipped by the
  conflict target never reaches `RETURNING`, so the count is exactly accepted-minus-deduped —
  not `len(batch)` or a rowcount. This is the concurrency-safe idempotency the dossier (§8)
  specifies, enforced by the DB's `UNIQUE(source_event_id)` index, not a racy read-then-write.
- Empty batch short-circuits to `0` (`:51`). `health` is stored as the enum's `.value`;
  `source` as `Provenance.model_dump()` (`:58-60`).

### `PostgresWatermarkRepository` — per-signal cursor, tz-aware UTC
- `advance` is a single upsert: `INSERT … ON CONFLICT (signal_key) DO UPDATE SET watermark=…`
  (`watermark_repository.py:56-63`) in `engine.begin()` — the row may or may not exist yet.
- `get` returns `None` before any advance, else the instant normalized to UTC via
  `value.astimezone(timezone.utc)` (`watermark_repository.py:50`): psycopg returns
  `timestamptz` already tz-aware in the session timezone, so callers never depend on that
  setting. Read path uses `engine.connect()` (no transaction needed).

### Testing convention (FK seeding)
- `observations.signal_key` and `watermarks.signal_key` FK into `signals.signal_key` with
  `ON DELETE RESTRICT`, and `signals.app_id` FKs into `apps`. Topology seeding (apps/signals
  from config) is a later story, so integration tests **hand-seed** a parent `apps`+`signals`
  row via raw psycopg (test arrangement) before exercising a repo
  (`test_persistence_adapters.py`, `seed_signal` helper).
- The `migrated_db` fixture is **session-scoped and shared** across the module, so tests use a
  per-test `signal_key` namespace to avoid cross-test row collisions/order-dependence.

## Inference (synthesis, not verified)
- `watermarks.updated_at` is set once at first insert and not refreshed by `advance`'s
  `DO UPDATE` (only `watermark` is set) — audit metadata only; nothing reads it today. Noted as
  a non-blocking minor at STORY-007 review.

## History
- sprint-3: created (compile pass folding STORY-007 — the first two repository adapters and
  their conventions: injected Engine, ON CONFLICT idempotency with RETURNING-based count,
  tz-aware-UTC watermark, FK-seeding in tests).
