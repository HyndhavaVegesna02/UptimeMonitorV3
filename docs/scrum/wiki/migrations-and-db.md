---
title: Migrations and the two-connection database split
code_refs: [alembic.ini, migrations/env.py, migrations/versions/eda70ac11454_baseline.py, migrations/versions/3a8254bcfe59_spine_schema.py, migrations/versions/eec78d2e8cbe_add_signals_component_id.py, migrations/versions/5ed254a8daab_add_signals_interval_seconds.py, backend/src/composition/settings.py, scripts/dev_db.py, backend/tests/conftest.py, scripts/check_fk_direction.py, backend/tests/test_spine_schema.py]
verified_sha: 143f15a
verified_sprint: sprint-47
status: archived
---

## Facts (verified against code)
- Alembic is initialized at the **repo top level** (dossier §4): `alembic.ini` + `migrations/`
  (with `migrations/env.py`, versions, etc.) — NOT under `backend/`.
- The baseline migration is `migrations/versions/eda70ac11454_baseline.py` — a real revision
  with `upgrade()`/`downgrade()` that creates NO tables. It is reversible: `downgrade base` →
  `upgrade head` round-trips to exit 0.
- **The spine schema migration** (STORY-006) is
  `migrations/versions/3a8254bcfe59_spine_schema.py` (`down_revision = eda70ac11454`). One
  reversible migration creates the full eleven-table spine (dossier §9) in three groups:
  - **topology** — `apps` (`config jsonb NOT NULL`), `signals`, `components`.
  - **signals** (runtime, append-only) — `observations`, `problem_signals`, `watermarks`
    (keyed by `signal_key`), `rejected_observations` (no FK to `signals`, by design — a
    rejected row may carry a `signal_key` that doesn't exist in topology, which is often why
    it was rejected).
  - **workflow** (runtime) — `status_proposals`, `approval_events`, `publications`,
    `maintenance_windows`.
  - Every timestamp column is `timestamptz`; `apps.config`, `observations.source`, and
    `rejected_observations.payload` are `jsonb`. `health` / `status` / proposal `state` are
    `text` + CHECK constraints mirroring the closed `Health` / `ComponentStatus` enums, not a
    Postgres ENUM type, so the Python enums stay the single source of truth.
  - Three required indexes: `UNIQUE` on `observations(source_event_id)`; composite index on
    `observations(signal_key, observed_at)`; and a **partial UNIQUE index**
    `uq_status_proposals_active_component` on `status_proposals(component_id)` filtered
    `WHERE state = 'open'` — enforcing at most one open ("active") proposal per component
    (dossier §9 → §11). Every FK declares an explicit `ON DELETE`: `RESTRICT` for any FK
    targeting seeded topology (`apps`, `signals`, `components`); `CASCADE` from
    `approval_events`/`publications` into their owning `status_proposals` row (a child record
    has no meaning once its proposal is gone). `downgrade()` drops every spine object; the
    round-trip `upgrade head` → `downgrade base` → `upgrade head` is tested directly.
- **The signals.component_id migration** (STORY-040) is `migrations/versions/eec78d2e8cbe_add_signals_component_id.py` (`down_revision = "3a8254bcfe59"`). One reversible migration adding a nullable `signals.component_id` column referencing `components.id` (with `ON DELETE RESTRICT`) and an index `ix_signals_component_id`. This allows signals to link to components in the database read model.
- **The signals.interval_seconds migration** (STORY-044, D1) is `migrations/versions/5ed254a8daab_add_signals_interval_seconds.py` (`down_revision = "eec78d2e8cbe"`, the current head). One reversible migration adding a NULLABLE `signals.interval_seconds` Integer column — no FK, no index. Nullable because a migration cannot read `config/` (config is composition's job) and must not invent a default: the column is backfilled by the boot seed (`composition/seed.py::seed_topology`, which now also carries `interval_seconds` in its `_SIGNALS` insert values and `on_conflict_do_update` `set_`) from `composition/config.py::SignalConfig.interval_seconds`. The `SignalRepository` port/adapter (see [[canonical-types-and-ports]], [[persistence-adapters]]) is the read side; a row whose `interval_seconds` is still `NULL` (seed never ran, or predates this migration) is surfaced honestly as `Signal.interval_seconds = None`, never guessed.
- **No `create_all` anywhere** — every table must arrive via an explicit migration. The only
  textual occurrences of `create_all` are comments in the baseline file forbidding it.
- **Two distinct connection env vars, never mixed** (dossier §3, §17):
  - `DATABASE_URL` — Neon **pooled** (PgBouncer); read by app runtime
    (`backend/src/composition/settings.py::APP_DATABASE_URL_VAR` / `backend/src/composition/settings.py::load_settings`) and by
    `scripts/check_fk_direction.py` (`scripts/check_fk_direction.py::main`).
  - `DATABASE_URL_DIRECT` — Neon **direct** (non-pooled); read by Alembic
    (`migrations/env.py`). DDL misbehaves through transaction pooling, so migrations run as a
    separate release step on the direct connection.
- App config / env-var reading lives in the **composition** zone
  (`backend/src/composition/settings.py`), never in `core/` — the import-linter boundary
  forbids core importing infrastructure. `load_settings()` raises `KeyError` if `DATABASE_URL`
  is unset (the app must not start without a DB URL). (The same module also hosts
  `load_live_secrets()` / `LiveSecrets` for the live loop's secrets — Dynatrace REQUIRED,
  Statuspage OPTIONAL since STORY-016b — plus, since STORY-045, the Statuspage-only subset
  `load_statuspage_secrets()` / `StatuspageSecrets` (`settings.py::load_statuspage_secrets`), which
  reads the SAME env-var names (`settings.py::STATUSPAGE_PAGE_ID_VAR` /
  `settings.py::STATUSPAGE_API_KEY_VAR`) and to which `load_live_secrets` now delegates its
  Statuspage half — used by `create_app`'s publisher wiring without requiring the DYNATRACE_* vars.
  All unrelated to the DB split; see [[dev-setup-and-dod]] and [[statuspage-publish]].)
- **URL dialect split (gotcha):** Alembic (SQLAlchemy 2) needs the psycopg3 dialect
  `postgresql+psycopg://…` (`migrations/env.py` normalizes to it); `scripts/check_fk_direction.py` uses
  raw psycopg and needs the plain libpq form `postgresql://…` (the `+psycopg` prefix makes
  raw psycopg raise). So against the same DB, set `DATABASE_URL_DIRECT` to the `+psycopg`
  form and `DATABASE_URL` to the plain form. The plain→`+psycopg`
  normalization for the SQLAlchemy-2 runtime engine has ONE home: `settings.py::to_psycopg_url`
  (STORY-040) — the app factory, the `seed_topology` CLI, and the test `engine` fixture all route
  through it instead of re-implementing the prefix swap.
- Sprint-0 / CI runs against a throwaway Dockerized `postgres:16` (host port 55432 for the
  manual one-liner / `scripts/dev_db.py up` CLI; an OS-assigned free port for the pytest
  fixture's spawned containers, see below); real Neon connection strings are deferred to the
  deployment zone (STORY-017).
- **Shared throwaway-DB harness (STORY-019):** `scripts/dev_db.py` centralizes the
  "start postgres:16 -> wait ready -> alembic upgrade head -> two-URL dialect split" sequence
  that this article's gotcha above used to require hand-rolling per brief. `up` emits both
  URLs already in the correct dialects (`DATABASE_URL` plain, `DATABASE_URL_DIRECT`
  `+psycopg`) — copy them as printed, no manual dialect juggling. The pytest session fixture
  `migrated_db` (`backend/tests/conftest.py`) wraps the same `dev_db.resolve_db()` decision
  logic: reuse external `DATABASE_URL`/`DATABASE_URL_DIRECT` if both are set (re-migrating to
  ensure current), else spawn a throwaway container if Docker is available (PID+UUID-unique
  name + free port, torn down in a finalizer even on test failure), else skip the DB-gated
  tests cleanly. `backend/tests/test_spine_schema.py` consumes this fixture instead of its own
  `skipif`/`conn` boilerplate.

## Inference (synthesis, not verified)
- `migrations/env.py` resolves the URL at import time, so any `alembic` subcommand (even
  `revision`) currently requires `DATABASE_URL_DIRECT` set — flagged as a possible ergonomics
  tweak later (see STORY-003 History).

## History
- sprint-0: created (STORY-003 Alembic + two-connection setup).
- sprint-2: updated (STORY-006 spine schema migration) — baseline Fact corrected (no longer
  forward-references STORY-006 as future work); added the `3a8254bcfe59_spine_schema` Fact
  describing the eleven-table spine, the three required indexes, and the explicit
  `ON DELETE` choices. `verified_sha` re-stamped to `54eb5c5`.
- sprint-3: updated (STORY-019 shared throwaway-DB harness) — added the `scripts/dev_db.py`
  Fact superseding the hand-rolled-per-brief one-liner this article's URL-dialect-split gotcha
  used to require, plus the `migrated_db` pytest fixture's reuse/spawn/skip decision logic.
  `verified_sha` re-stamped accordingly.
- sprint-18: updated (STORY-040 config topology boot seeding) — added `eec78d2e8cbe_add_signals_component_id.py` migration to link signals to components. `verified_sha` re-stamped to `19eefc8`.
- sprint-20: re-verified (STORY-016). No migration or DB-split change; `settings.py` gained
  `load_live_secrets`/`LiveSecrets` (live-loop secrets, unrelated to the DB connection split).
  `verified_sha` re-stamped to `d9c2a77`.
- sprint-21: re-verified (STORY-016b). No migration or DB-split change; `load_live_secrets` now requires
  only the two Dynatrace vars (Statuspage optional). `verified_sha` re-stamped to `213034b`.
- sprint-29: re-verified (STORY-045). No migration or DB-split change; `settings.py` gained the
  `StatuspageSecrets`/`load_statuspage_secrets` subset (env-var names hoisted to
  `STATUSPAGE_PAGE_ID_VAR`/`STATUSPAGE_API_KEY_VAR`; `load_live_secrets` delegates) for
  `create_app`'s publisher wiring. `verified_sha` re-stamped to `7cabee7`.
- sprint-30 (STORY-044): added `migrations/versions/5ed254a8daab_add_signals_interval_seconds.py`
  (new head, `down_revision = "eec78d2e8cbe"`) — a nullable `signals.interval_seconds` Integer
  column, backfilled by the boot seed rather than a migration-time default (D1). No DB-split
  change. `verified_sha` re-stamped to `280c1e3`.
- sprint-43 (STORY-073, re-verify): `scripts/dev_db.py` gained the robust tunable container
  readiness (`DEV_DB_READY_TIMEOUT_SECONDS`, retry/backoff) — this article's shared-harness
  description was unaffected (see [[dev-setup-and-dod]] for the readiness-specific Facts); no
  migration or two-connection-split Fact changed. `verified_sha` re-stamped to `10a2d73` (this
  article had drifted un-bumped through the STORY-073 code change; caught by the Sprint 43
  quality-review wiki sweep).
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged two uncovered
  citations: `CLAUDE.md` (cited alongside the URL-dialect-split gotcha as also documenting it) and
  `backend/tests/test_spine_schema.py` (the DB-gated migration round-trip test — `upgrade head` →
  `downgrade base` → `upgrade head`). Both genuinely define this article's subject (the migration
  schema and its documented two-connection split); added to `code_refs`. No Fact text changed.
  `verified_sha` re-stamped to `678ff0d`.
- sprint-44 (STORY-079 fix loop, quality review MAJOR): the sprint-44 quality review found
  `CLAUDE.md` over-broad in `code_refs` — it is the hottest doc in the repo and the
  URL-dialect-split contract is already pinned by `migrations/env.py`, `settings.py`, and
  `check_fk_direction.py` refs, so a `CLAUDE.md` edit unrelated to this contract would falsely
  flag this article stale. Removed `CLAUDE.md` from `code_refs`; struck the now-uncovered
  parenthetical pointer "(Documented in `CLAUDE.md`.)" from the URL-dialect-split gotcha Fact
  (the substantive claim text is unchanged). `verified_sha` re-stamped to `adc002a`.
- sprint-46 (STORY-082/083): Re-verified after settings and conftest adjustments for DynamoDB Local support. verified_sha -> 7097bcc.
- sprint-47 (STORY-080): Re-verified after hardening test-db connection readiness and collision-proofing CLI test container names and ports. verified_sha -> 50a7bd9.
