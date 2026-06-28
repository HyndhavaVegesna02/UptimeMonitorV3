---
id: STORY-040
title: Topology seed + signal→component migration — Neon as the read model (incl. boot wiring)
type: feature
---

## Context
Spec: dossier §7 (Option C / D6 — Neon is a **read model** seeded from Git-versioned config at boot,
via fail-fast validation + idempotent upsert keyed on stable ids) + §9 (spine) + §17 (boot:
migrate → seed → serve). The DB-seed half of the original STORY-040; the config-reading half is
**STORY-040a** (the `Config` aggregate + `load_config` + resolvers), a prerequisite — DONE.

**Why this story:** today nothing populates the spine, so `GET /api/v1/components` returns `[]` and the
orchestration's `ComponentRepository.get` finds nothing. This seeds apps/components/signals from config
into Neon and adds the spine's missing signal→component link, so the dashboard shows real components
and the orchestration can resolve current status. **PO chose to include the app-startup wiring** (the
booting app self-seeds), not just the seed function/CLI.

## Refinement decisions (grounded in the schema + config layer, 2026-06-28)
- **signal→component link = a nullable `component_id` FK on `signals`** → `components.id`
  (`ON DELETE RESTRICT`). Both `signals` and `components` are in the `check_fk_direction.py` SPINE
  allowlist, so this spine→spine FK does NOT trip the FK-direction gate. Nullable for migration safety
  (the table may have rows; the config layer already guarantees every seeded signal has a component).
- **The seed must NOT clobber `components.status`** — status is RUNTIME state (owned by the
  approve/publish flow). The component upsert updates `name`/`app_id`/`updated_at` only; `status` is
  left alone (new rows take the schema default `operational`). Re-seeding never resets a live status.
- **`apps.config` is `jsonb NOT NULL`** — the seed writes the app's behavioral config (its
  `AntiFlapThresholds` as JSON, e.g. `{"thresholds": {...}}`) into it.
- **`load_config(config_dir)` globs `config_dir/*.yaml`** — point it at `config/apps`. `create_app`'s
  default `config_dir` is `config/apps` (overridable via a `CONFIG_DIR` setting).
- **Seed uses the pooled `DATABASE_URL`** (it is DML, not DDL — unlike Alembic which needs DIRECT).

## Description
1. **Migration** (new Alembic revision, `down_revision` = the spine schema): add nullable
   `signals.component_id` `ForeignKey(components.id, ondelete="RESTRICT")` + index. Reversible
   (`downgrade` drops it). `check_fk_direction.py` stays green (spine→spine).
2. **`composition/seed.py::seed_topology(config: Config, engine: Engine) -> None`**: idempotent upsert,
   in FK order apps → components → signals:
   - `apps`: `INSERT (id, config) ON CONFLICT (id) DO UPDATE SET config=…, updated_at=now()`.
   - `components`: `INSERT (id, app_id, name) ON CONFLICT (id) DO UPDATE SET name=…, app_id=…,
     updated_at=now()` — **never `status`**.
   - `signals`: `INSERT (signal_key, app_id, name, component_id) ON CONFLICT (signal_key) DO UPDATE
     SET app_id=…, name=…, component_id=…, updated_at=now()`.
   Composition-zone (imports core/adapters/config); no business logic.
3. **`scripts/seed_topology.py`** CLI (mirrors `scripts/check_fk_direction.py` / `dev_db.py`):
   `load_config(CONFIG_DIR or config/apps)` + build an `Engine` from `DATABASE_URL` + `seed_topology`;
   clear errors + nonzero exit on failure.
4. **App-startup wiring:** `create_app(config_dir=None, …)` — in the real (non-injected) branch,
   `load_config(config_dir or <CONFIG_DIR/"config/apps">)` and store `app.state.seed_config` (fail-fast:
   a bad config raises at construction); the `lifespan` STARTUP (before `yield`) calls
   `seed_topology(app.state.seed_config, app.state.db_engine)` when both are present. Injected/test
   branch sets `seed_config=None` → no seed. A `CONFIG_DIR` setting is added to `composition/settings.py`
   (optional, default `config/apps`).

## Acceptance Criteria (refined — PO-approved 2026-06-28)
- [ ] AC1 (migration): a reversible Alembic migration adds nullable `signals.component_id`
      FK→`components.id`; `alembic upgrade head` + `downgrade` round-trip exit 0;
      `python scripts/check_fk_direction.py` stays green (spine→spine, not flagged).
- [ ] AC2 (idempotent seed): `seed_topology(config, engine)` upserts apps/components/signals from a
      `Config`; running it TWICE on unchanged config is a no-op (asserted against a throwaway DB —
      row counts + values stable). Signals get their `component_id`. (DB-gated.)
- [ ] AC3 (status preserved): set a seeded component's `status` to `degraded`, re-run `seed_topology`
      on unchanged config → the component's `status` is STILL `degraded` (topology re-seed never resets
      runtime status). (DB-gated.)
- [ ] AC4 (boot wiring + dashboard): `create_app` with a real engine + a `config_dir` seeds on startup;
      after startup, `GET /api/v1/components` returns the seeded components (TestClient over a migrated
      throwaway DB). A bad/invalid config dir makes `create_app` (or startup) fail FAST.
- [ ] AC5 (CLI): `scripts/seed_topology.py` seeds a throwaway DB from `config/apps` and exits 0; a
      load/validation failure exits nonzero with a clear message.
- [ ] AC6 (full SIX-command DoD gate green). Forward blast radius (the MECHANICAL sweep): migrations
      article (new revision + the signal→component link), config-layer (the seed consumer),
      persistence/architecture as flagged — updated + re-verified.

## Conventions checklist
- Docstrings cite §7/§9/§17; `seed.py` is composition wiring (no domain logic); core untouched.
- Idempotency + status-preservation + fail-fast tested; DB-gated tests isolate (STORY-039 truncate
  fixture covers runtime tables; this story's tests must also clean apps/components/signals or use the
  throwaway-DB so a reused DB stays green — extend the cleanup to topology tables it seeds).
- `src` never imports `tests`; scoped staging; no sentinel mappings.

## Open Questions
- Whether `CONFIG_DIR` defaults to `config/apps` (loader globs that dir) or `config` (loader would need
  to recurse) — RESOLVED: `config/apps` (loader globs `config_dir/*.yaml`). Confirm at implementation.
- Estimate: **5** (migration + seed + CLI + startup wiring + settings + DB tests; top of range).

## History
- 2026-06-28: created (Sprint 15) then reframed (Sprint 16) to the DB-seed half. Refined at Sprint 18
  planning: nullable component_id FK (spine→spine), status-preservation on re-seed, apps.config JSON,
  config_dir=config/apps, app-startup wiring INCLUDED (PO). Estimate 5. Status: draft → ready.
