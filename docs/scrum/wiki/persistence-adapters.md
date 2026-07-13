---
title: Persistence adapters — the repository implementations
code_refs: [backend/src/adapters/persistence/observation_repository.py, backend/src/adapters/persistence/watermark_repository.py, backend/src/adapters/persistence/rejected_observation_repository.py, backend/src/adapters/persistence/proposal_repository.py, backend/src/adapters/persistence/component_repository.py, backend/src/adapters/persistence/maintenance_repository.py, backend/src/adapters/persistence/publication_repository.py, backend/src/adapters/persistence/signal_repository.py, backend/tests/test_persistence_adapters.py, backend/tests/test_component_repository_contract.py, backend/tests/test_signal_repository_contract.py, backend/src/core/queries/availability.py, migrations/versions/ecda752c8865_add_publications_outcome.py, migrations/versions/a2c1d89efcea_add_observations_response_status_code.py, backend/tests/conftest.py, backend/tests/fakes.py]
verified_sha: f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787
verified_sprint: sprint-45
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
- STORY-064: `_OBSERVATIONS` (`observation_repository.py::_OBSERVATIONS`) gained a
  `response_status_code` column (nullable Integer, migration
  `a2c1d89efcea_add_observations_response_status_code.py`, see [[migrations-and-db]]);
  `save_new`'s values dict now includes `observation.response_status_code` verbatim (int or
  `None`) — no serialization needed, unlike `source`/`health`.

### `PostgresObservationRepository.in_window` — the read side (STORY-011, dossier §11)
- A plain `SELECT` over `_OBSERVATIONS` filtered to one `signal_key` and the half-open range
  `observed_at >= since AND observed_at < until` (`observation_repository.py::PostgresObservationRepository.in_window`), run on
  `sa.Engine.connect` (read-only, no transaction needed) — mirrors `PostgresWatermarkRepository.get`'s read-path convention. Half-open `[since, until)` means adjacent calendar windows
  (e.g. two consecutive 24h reporting windows) never double-count the boundary instant.
- This is the ONLY read path `core/queries/availability.py`'s `AvailabilityCalculator` uses
  (see [[canonical-types-and-ports]]) — all SQL for the availability engine's data access
  lives here, never in core.
- Reconstructs canonical `SignalObservation`s row-by-row (`observation_repository.py::PostgresObservationRepository.in_window`): `health` from its
  stored `.value` string via `Health(row.health)`, `source` from its stored `JSONB` dict via
  `Provenance(**row.source)`, and `observed_at` re-normalized to UTC via
  `.astimezone(timezone.utc)` — the same psycopg tz-aware-`timestamptz` convention `get`
  already relies on (`watermark_repository.py::PostgresWatermarkRepository.get`). The core never sees a raw row or a driver-specific type.
  STORY-064: also selects/reconstructs `response_status_code` (int or `NULL` passed straight
  through, no mapping).
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
- `get` (`proposal_repository.py::PostgresProposalRepository.get`) SELECTs a proposal by `id`, returning
  `None` if absent (STORY-014: the lookup `ApprovalService` uses before resolving).
- `resolve` (`proposal_repository.py::PostgresProposalRepository.resolve`) UPDATEs `state`/`reason`/`resolved_at` only `WHERE id =
  :id AND state = 'open'`, and raises `ProposalNotOpenError` (a domain error; STORY-014 — was a bare
  `ValueError`) if `rowcount != 1` — so re-resolving an already-terminal proposal, an unknown id, or a
  lost-race concurrent resolve fails loudly rather than silently clobbering (STORY-012 fix loop 1), and
  the edge maps it to HTTP 409 rather than 500. `FakeProposalRepository.resolve` raises the same
  `ProposalNotOpenError`, so fake and adapter agree (parity).
- `record_approval_event` INSERTs a new record into `approval_events` (`proposal_repository.py::PostgresProposalRepository.record_approval_event`).
- `list_open` (`proposal_repository.py::PostgresProposalRepository.list_open`) SELECTs all open proposals `WHERE state = 'open'` (STORY-014b). Returns `[]` if none exist.

### `PostgresComponentRepository` — components listing, lookup, and status write-back (STORY-014b, STORY-016a, STORY-045)
- Implements `ComponentRepository` port against `components` table (`component_repository.py::PostgresComponentRepository`).
- `list_components` (`component_repository.py::PostgresComponentRepository.list_components`) SELECTs `id`, `name`, `status`, `app_id` and maps `status` text to `ComponentStatus`. Returns `[]` if none exist.
- `get` (`component_repository.py::PostgresComponentRepository.get`) SELECTs a component by `id` (STORY-016a), returning `None` if absent (fake/adapter parity).
- `set_status` (`component_repository.py::PostgresComponentRepository.set_status`, STORY-045) is a single conditional `UPDATE components SET status = ... WHERE id = ...` run in `sa.Engine.begin`; `rowcount == 0` raises `ComponentNotFoundError` (`core/domain/component.py::ComponentNotFoundError`) rather than silently no-op'ing (2026-06-28 check-then-act agreement) — mirrors `PostgresProposalRepository.resolve`'s conditional-write-then-guard shape. `FakeComponentRepository.set_status` (`backend/tests/fakes.py`) raises the identical error on an unknown id (2026-06-26 fake/adapter parity agreement); ONE shared contract test body (`backend/tests/test_component_repository_contract.py::_assert_set_status_contract`) is run against BOTH implementations (the Postgres half DB-gated via `migrated_db`), proving a known id's update is visible via `get` and an unknown id raises `ComponentNotFoundError` from both. Called by the composition-layer `StatusWritebackPublisher` decorator (see [[statuspage-publish]]) right before the best-effort external publish, at both the approve trigger and the recovery trigger.

### `PostgresMaintenanceRepository` — maintenance scheduling (STORY-036; STORY-065, sprint-45)
- Implements `MaintenanceRepository` port against `maintenance_windows` table (`maintenance_repository.py::PostgresMaintenanceRepository`).
- `list_windows` (`maintenance_repository.py::PostgresMaintenanceRepository.list_windows`) SELECTs scheduled windows (including `title`) ordered by `starts_at` and maps them to `MaintenanceWindow` domain objects. Returns `[]` if none exist.
- `create` (`maintenance_repository.py::PostgresMaintenanceRepository.create`) INSERTs a new maintenance window (including `title`) and returns it with the database-assigned `id`.
- `is_under_maintenance` (`maintenance_repository.py::PostgresMaintenanceRepository.is_under_maintenance`) checks if a component is active under maintenance at a given timestamp using inclusive start and exclusive end boundaries (`starts_at <= at < ends_at`).
- `delete` (`maintenance_repository.py::PostgresMaintenanceRepository.delete`, STORY-065, sprint-45) DELETEs a maintenance window by `id`; raises `MaintenanceWindowNotFoundError` if zero rows are affected. `FakeMaintenanceRepository` mirrors this behavior.

### `PostgresSignalRepository` — read-only seeded-topology signal access (STORY-044)
- Implements `SignalRepository` port against the `signals` table (`signal_repository.py::PostgresSignalRepository`).
  Read-only: SELECTs only, mirroring `PostgresComponentRepository`'s style (injected `Engine`,
  lightweight `sa.table` construct, no ORM model) — the seed (`composition/seed.py::seed_topology`)
  is the only writer.
- `list_signals` (`signal_repository.py::PostgresSignalRepository.list_signals`) SELECTs `signal_key`,
  `name`, `component_id`, `interval_seconds`, ordered by `signal_key` (deterministic). Returns `[]`
  if none exist.
- `get` (`signal_repository.py::PostgresSignalRepository.get`) SELECTs a signal by key, returning
  `None` if absent (fake/adapter parity, 2026-06-26). A `NULL interval_seconds` column value
  surfaces as `Signal.interval_seconds = None` — never guessed or defaulted here.
- Fake/adapter parity (2026-06-26): `FakeSignalRepository` (`backend/tests/fakes.py`) and
  `PostgresSignalRepository` agree on: empty → `[]`; `list_signals` ordered by `signal_key`; `get`
  on an unknown key → `None`; `get` on a known key returns all four fields incl. a NULL
  `interval_seconds` as `None`. ONE shared assertion body
  (`backend/tests/test_signal_repository_contract.py::_assert_signal_repository_contract`) is run
  against both implementations (the Postgres half DB-gated via `migrated_db`, seeded through raw
  SQL — topology seeding via `seed_topology` is a heavier alternative not needed for this
  read-only contract).

### `PostgresPublicationRepository` — publish-attempt recording (STORY-037; STORY-072 record-always; STORY-066, sprint-45)
- Implements `PublicationRepository` port against the `publications` table (`publication_repository.py::PostgresPublicationRepository`). The table's `outcome` column was added by `migrations/versions/ecda752c8865_add_publications_outcome.py` (STORY-072, see [[statuspage-publish]], [[migrations-and-db]]) — NOT the original spine migration.
- `record` (`publication_repository.py::PostgresPublicationRepository.record`) INSERTs a new publication row (including `outcome`) via `INSERT … RETURNING` and returns the persisted `Publication` with the database-assigned `id`. Called on EVERY publish ATTEMPT (STORY-072) — `publication.outcome` (`PublicationOutcome.SUCCEEDED`/`FAILED`) distinguishes a successful publish from a raising delegate; the `ck_publications_outcome` CHECK constraint enforces the closed vocabulary at the DB level.
- `list_recent` (`publication_repository.py::PostgresPublicationRepository.list_recent`) SELECTs up to `limit` (default 50) publications (including `outcome`) ordered by `published_at DESC` (most-recent-first), selecting `author` via a correlated scalar subquery over `approval_events`. Returns `[]` when none exist. Used by the Publications tab (§17).
- Fake/adapter parity (2026-06-26; re-verified STORY-072, STORY-066): `FakePublicationRepository` and `PostgresPublicationRepository` agree on: empty → `[]`, `record` returns a persisted row with `id`, `list_recent` is most-recent-first (ordered by `published_at DESC`), both agree on `outcome` recorded, and (STORY-066) both agree on `author` derived on read — `FakePublicationRepository` accepts a `proposal_to_actor` map in its constructor to resolve `author` dynamically on `list_recent`.

### Testing convention (FK seeding)
- `observations.signal_key` and `watermarks.signal_key` FK into `signals.signal_key` with
  `ON DELETE RESTRICT`, and `signals.app_id` FKs into `apps`. Topology seeding (apps/signals
  from config) is implemented in sprint-18, so integration tests either use `seed_topology` or **hand-seed** a parent `apps`+`signals`
  row via raw psycopg (test arrangement) before exercising a repo
  (`test_persistence_adapters.py`, `seed_signal` helper).
- `status_proposals.component_id`, `maintenance_windows.component_id`, and `publications.component_id` FK into `components.id`, which FKs into `apps.id`. Integration
  tests hand-seed parent `apps` + `components` rows via a raw psycopg helper `seed_component` before
  exercising the proposal/maintenance/publication repository adapters.
- `rejected_observations` has no FK, so its tests skip seeding entirely.
- The `migrated_db` fixture is **session-scoped and shared**, but a function-scoped
  `clean_runtime_tables` fixture (`backend/tests/conftest.py`, STORY-039) **truncates the runtime
  tables** (`rejected_observations`, `observations`, `watermarks`, `problem_signals`) before each
  DB-gated test, so the suite is order- and reused-DB-independent.
- Tests specifically verifying `seed_topology` or CLI execution clean up the topology tables (`apps`, `components`, `signals`) before and after each test run using a cascaded truncation (`TRUNCATE TABLE apps, components, signals CASCADE;`) to keep the shared database clean.

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
  `SELECT` the new availability engine (`core/queries/availability.py`) reads through; no
  schema change, no new migration.
- sprint-9: STORY-012 adds `PostgresProposalRepository` for workflow proposal storage and resolution.
- sprint-12: STORY-014 adds `PostgresProposalRepository.get(proposal_id)`; `resolve` now raises the
  `ProposalNotOpenError` domain error (was a bare `ValueError`) so a lost-race resolve maps to HTTP 409.
  Re-verified at eb147ef.
- sprint-14: STORY-036 adds `PostgresMaintenanceRepository` for scheduled maintenance windows. Re-verified at 8e15534.
- sprint-18: updated (STORY-040 — added description of `seed_topology` idempotent seeding and the clean_topology testing convention). verified_sha = 19eefc8.
- sprint-19: STORY-037 adds `PostgresPublicationRepository` against the existing `publications` table (no migration). `record` INSERTs + RETURNS; `list_recent` SELECTs ORDER BY `published_at DESC`. DB-gated test in `test_persistence_adapters.py::test_postgres_publication_repository` truncates `publications` for isolation. verified_sha → cc7f0ce.
- sprint-29 (STORY-045): adds `PostgresComponentRepository.set_status` (a conditional `UPDATE` raising `ComponentNotFoundError` on 0 rows) and the identical `FakeComponentRepository.set_status`, proven by a new shared contract test file (`backend/tests/test_component_repository_contract.py`, added to `code_refs`). No migration — `components.status` already existed; it was simply never written after seeding until this story. verified_sha → 7cabee7.
- sprint-30 (STORY-044): adds `PostgresSignalRepository` (`adapters/persistence/signal_repository.py`,
  read-only: `list_signals` + `get` against the `signals` table, now including the D1-added
  `interval_seconds` column) and the identical `FakeSignalRepository`, proven by a new shared
  contract test file (`backend/tests/test_signal_repository_contract.py`, added to `code_refs`).
  verified_sha → 280c1e3.
- sprint-39 (STORY-071, defect fix, mechanical staleness sweep): `PostgresProposalRepository` and
  `record_approval_event` are UNCHANGED — the defect (approve/reject 500 on
  `ck_approval_events_action`) was in the calling `core/services/approval.py::ApprovalService`,
  which passed the wrong `action` literal into this repository's INSERT (see
  [[api-five-file-convention]]). `test_persistence_adapters.py` (in `code_refs`) gained two
  DB-gated regression tests: one driving a real approve AND reject through the real
  `ApprovalService` + `PostgresProposalRepository` against the live Postgres constraint (confirmed
  failing with `CheckViolation` before the fix), and one asserting the fake and real repository
  agree on the recorded `action` (fake/adapter parity). No new fact about this adapter's own
  behavior — `record_approval_event` always INSERTed whatever `action` string it was given; it was
  never at fault. verified_sha → 06cf232.
- sprint-40 (STORY-072, record-always publication outcome): `PostgresPublicationRepository` now
  DOES have a migration behind it — `migrations/versions/ecda752c8865_add_publications_outcome.py`
  adds `publications.outcome` (see [[statuspage-publish]], [[migrations-and-db]]) — correcting the
  STORY-037-era "existing table, no migration" fact (Facts updated above). `record`/`list_recent`
  now read/write `outcome`; `FakePublicationRepository` needed no code change (fake/adapter parity
  held automatically via `model_copy`). Three new DB-gated tests in `test_persistence_adapters.py`:
  `test_postgres_publication_repository_records_failed_outcome` (real round-trip of an explicit
  FAILED record), `test_publications_outcome_check_constraint_allows_values_rejects_others` (drives
  `ck_publications_outcome` directly — both allowed values insert, a disallowed one raises
  `psycopg.errors.CheckViolation` — the STORY-071 retro lesson), and
  `test_recording_publisher_records_exactly_one_row_via_real_postgres_success_and_failure` (the real
  `RecordingPublisher`+`BestEffortPublisher` chain against real Postgres, both paths, exactly one row
  each). verified_sha → a1bacab.
- sprint-43 (STORY-078): Repointed availability file references to core/queries/availability.py. verified_sha → 05f640e.
- sprint-43 (quality-review fix loop, M2/m3): `observation_repository.py`'s `in_window` docstring's
  remaining stale `core/services/availability.py` reference repointed to
  `core/queries/availability.py` (STORY-078 follow-up); `core/queries/availability.py`'s module
  docstring restored (see [[core-pipeline-and-availability]] for detail). No SQL or repository
  behavior changed. verified_sha -> 10a2d73.
- sprint-44 (STORY-064, pilot): `PostgresObservationRepository`'s `_OBSERVATIONS` table construct,
  `save_new`, and `in_window` all gained `response_status_code` (nullable Integer, new migration
  `a2c1d89efcea_add_observations_response_status_code.py`, new head off `ecda752c8865`) --
  Facts updated above. `FakeObservationRepository` needed NO code change (it already round-trips
  every `SignalObservation` field via storing the whole object) -- ONE shared contract test body
  (`test_persistence_adapters.py::_assert_response_status_code_round_trips`) is run against BOTH
  implementations, proving a present int and an explicit `None` both round-trip identically (fake/
  adapter parity). `code_refs` += the new migration file. verified_sha -> 0da9568.
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged two uncovered
  citations: `backend/tests/conftest.py` (the `clean_runtime_tables` fixture the FK-seeding testing
  convention section describes) and `backend/tests/fakes.py` (`FakeComponentRepository.set_status`,
  `FakeSignalRepository`, `FakeObservationRepository` — the fake halves of the parity contracts this
  article documents). Both genuinely define the fake/adapter-parity subject; added to `code_refs`.
  No Fact text changed. verified_sha -> 678ff0d.
- sprint-45 (STORY-065/STORY-066): verified after implementing Maintenance title + DELETE endpoint and Publication author metadata. MaintenanceRepository gained `delete`, and PublicationRepository.list_recent gained correlated subquery for author, both with fake/adapter parity tests. verified_sha -> f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787.


