---
title: Persistence adapters — the repository implementations
code_refs: [backend/src/adapters/persistence/observation_repository.py, backend/src/adapters/persistence/watermark_repository.py, backend/src/adapters/persistence/rejected_observation_repository.py, backend/src/adapters/persistence/proposal_repository.py, backend/tests/test_persistence_adapters.py, backend/src/core/services/availability.py]
verified_sha: a37e21e
verified_sprint: sprint-12
status: verified
---

## Facts (verified against code)

The concrete Postgres implementations of the core's persistence ports (STORY-007, STORY-009,
Zone 2). They live ONLY in `backend/src/adapters/persistence/`; all SQL stays here (the
`core-independence` contract forbids `sqlalchemy` in `src.core`). Each imports inward
(`src.core.ports`, `src.core.domain`) and never another adapter.

### Convention: injected SQLAlchemy `Engine`, never a global
- All three repositories take an `Engine` in `__init__` and store it on `self._engine`
  (`observation_repository.py::PostgresObservationRepository.__init__`, `watermark_repository.py::PostgresWatermarkRepository.__init__`,
  `rejected_observation_repository.py::PostgresRejectedObservationRepository.__init__`). There is no module-global engine and no
  composition wiring yet — tests construct the engine from the `migrated_db` fixture's URL
  (converted to the `postgresql+psycopg://` dialect for SQLAlchemy 2). A real
  composition-root engine factory is a later story.
- Tables are declared as lightweight `sa.table(...)`/`sa.column(...)` constructs, NOT ORM
  models (`observation_repository.py::_OBSERVATIONS`, `watermark_repository.py::_WATERMARKS`,
  `rejected_observation_repository.py::_REJECTED_OBSERVATIONS`) — there are no SQLAlchemy models in this project;
  the schema's source of truth is the Alembic migration `3a8254bcfe59` (see
  [[migrations-and-db]]). Any `jsonb` column must be typed `JSONB` on the construct
  (`observation_repository.py::_OBSERVATIONS`, `rejected_observation_repository.py::_REJECTED_OBSERVATIONS`) or psycopg3
  raises `cannot adapt type 'dict'`.

### `PostgresObservationRepository.save_new` — DB-level idempotency
- `INSERT … ON CONFLICT (source_event_id) DO NOTHING … RETURNING source_event_id`
  (`observation_repository.py::PostgresObservationRepository.save_new`), run inside `sa.Engine.begin` (one commit).
- The **newly-inserted count** is `len(result.fetchall())` (`observation_repository.py::PostgresObservationRepository.save_new`): a row skipped by the
  conflict target never reaches `RETURNING`, so the count is exactly accepted-minus-deduped —
  not `len(batch)` or a rowcount. This is the concurrency-safe idempotency the dossier (§8)
  specifies, enforced by the DB's `UNIQUE(source_event_id)` index, not a racy read-then-write.
- Empty batch short-circuits to `0` (`observation_repository.py::PostgresObservationRepository.save_new`). `health` is stored as the enum's `.value`;
  `source` as `Provenance.model_dump()` (`observation_repository.py::PostgresObservationRepository.save_new`).

### `PostgresObservationRepository.in_window` — the read side (STORY-011, dossier §11)
- A plain `SELECT` over `_OBSERVATIONS` filtered to one `signal_key` and the half-open range
  `observed_at >= since AND observed_at < until` (`observation_repository.py::PostgresObservationRepository.in_window`), run on
  `sa.Engine.connect` (read-only, no transaction needed) — mirrors `PostgresWatermarkRepository.get`'s read-path convention. Half-open `[since, until)` means adjacent calendar windows
  (e.g. two consecutive 24h reporting windows) never double-count the boundary instant.
- This is the ONLY read path `core/services/availability.py`'s `AvailabilityCalculator` uses
  (see [[canonical-types-and-ports]]) — all SQL for the availability engine's data access
  lives here, never in core.
- Reconstructs canonical `SignalObservation`s row-by-row (`observation_repository.py::PostgresObservationRepository.in_window`): `health` from its
  stored `.value` string via `Health(row.health)`, `source` from its stored `JSONB` dict via
  `Provenance(**row.source)`, and `observed_at` re-normalized to UTC via
  `.astimezone(timezone.utc)` — the same psycopg tz-aware-`timestamptz` convention `get`
  already relies on (`watermark_repository.py::PostgresWatermarkRepository.get`). The core never sees a raw row or a driver-specific type.
- An unknown/never-ingested `signal_key`, or a window with no matching rows, returns `[]` —
  no error, no `None` — consistent with the AC6 degenerate-input contract the availability
  engine depends on.

### `PostgresWatermarkRepository` — per-signal cursor, tz-aware UTC
- `advance` is a single upsert: `INSERT … ON CONFLICT (signal_key) DO UPDATE SET watermark=…`
  (`watermark_repository.py::PostgresWatermarkRepository.advance`) in `sa.Engine.begin` — the row may or may not exist yet.
- `get` returns `None` before any advance, else the instant normalized to UTC via
  `value.astimezone(timezone.utc)` (`watermark_repository.py::PostgresWatermarkRepository.get`): psycopg returns
  `timestamptz` already tz-aware in the session timezone, so callers never depend on that
  setting. Read path uses `sa.Engine.connect` (no transaction needed).

### `PostgresRejectedObservationRepository.save` — the quarantine sink (STORY-009)
- A plain `INSERT` (no conflict handling — there is no idempotency key on this table; every
  rejection is its own row), run inside `sa.Engine.begin`
  (`rejected_observation_repository.py::PostgresRejectedObservationRepository.save`).
- `signal_key` is accepted as `None` and inserted as SQL `NULL` — the `rejected_observations`
  column is nullable with deliberately NO FK (see [[migrations-and-db]]), so a quarantined
  row with an unknown/absent signal_key (often exactly *why* it was rejected) is still
  insertable without seeding any parent topology row first.
- `payload` is whatever dict the caller passes (the core's `IngestService` passes
  `SignalObservation.model_dump(mode="json")` — already JSON-safe: datetimes as ISO strings,
  enums as their `.value`) — the adapter does no serialization of its own beyond the `JSONB`
  column typing.

### `PostgresProposalRepository` — workflow persistence (STORY-012, dossier §12)
- Implements `ProposalRepository` port against `status_proposals` and `approval_events` tables.
- `create_open` (`proposal_repository.py::PostgresProposalRepository.create_open`) inserts a proposal via `ON CONFLICT (component_id) DO
  NOTHING` on the partial unique index active when `state = 'open'`. Returns `None` (with a debug
  log) if a conflict occurs (a concurrent open already exists), else the new proposal.
- `get_open` SELECTs the single open proposal for `component_id` (`proposal_repository.py::PostgresProposalRepository.get_open`).
- `resolve` (`proposal_repository.py::PostgresProposalRepository.resolve`) UPDATEs `state`/`reason`/`resolved_at` only `WHERE id =
  :id AND state = 'open'`, and raises `ValueError` if `rowcount != 1` — so re-resolving an
  already-terminal proposal or an unknown id fails loudly rather than silently clobbering (STORY-012
  fix loop 1). `FakeProposalRepository.resolve` raises the same way, so fake and adapter agree.
- `record_approval_event` INSERTs a new record into `approval_events` (`proposal_repository.py::PostgresProposalRepository.record_approval_event`).

### Testing convention (FK seeding)
- `observations.signal_key` and `watermarks.signal_key` FK into `signals.signal_key` with
  `ON DELETE RESTRICT`, and `signals.app_id` FKs into `apps`. Topology seeding (apps/signals
  from config) is a later story, so integration tests **hand-seed** a parent `apps`+`signals`
  row via raw psycopg (test arrangement) before exercising a repo
  (`test_persistence_adapters.py`, `seed_signal` helper).
- `status_proposals.component_id` FKs into `components.id`, which FKs into `apps.id`. Integration
  tests hand-seed parent `apps` + `components` rows via a raw psycopg helper `seed_component` before
  exercising the proposal repo adapter.
- `rejected_observations` has no FK, so its tests skip seeding entirely.
- The `migrated_db` fixture is **session-scoped and shared** across the module, so tests use a
  per-test `signal_key` and `component_id` namespace to avoid cross-test row collisions/order-dependence.

## Inference (synthesis, not verified)
- `watermarks.updated_at` is set once at first insert and not refreshed by `advance`'s
  `DO UPDATE` (only `watermark` is set) — audit metadata only; nothing reads it today. Noted as
  a non-blocking minor at STORY-007 review.

## History
- sprint-3: created (compile pass folding STORY-007 — the first two repository adapters and
  their conventions: injected Engine, ON CONFLICT idempotency with RETURNING-based count,
  tz-aware-UTC watermark, FK-seeding in tests).
- sprint-5: STORY-009 adds `PostgresRejectedObservationRepository` (the quarantine-sink
  adapter) and its no-FK testing convention.
- sprint-7: STORY-011 adds `PostgresObservationRepository.in_window` — the half-open-range
  `SELECT` the new availability engine (`core/services/availability.py`) reads through; no
  schema change, no new migration.
- sprint-9: STORY-012 adds `PostgresProposalRepository` for workflow proposal storage and resolution.

