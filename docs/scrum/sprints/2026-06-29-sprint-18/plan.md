# Sprint 18 — Plan

**Goal:** Make Neon the seeded read model (dossier §7 Option C) — add the `signals.component_id`
migration, an idempotent `seed_topology` upsert, a CLI, and app-startup seed wiring — so the spine is
populated from `config/apps` and `GET /api/v1/components` shows real components.

**Branch:** `sprint-18` · **Start tag:** `sprint-18-start` · **Baseline:** `44eaf43` (refinement on
branch; from main `9aed7b2`).

**Committed: 5 pts** — STORY-040 (single-story sprint).

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)
The PO implements externally onto `sprint-18`, OR (quota permitting) the orchestrator finishes via a
**Sonnet** implementer subagent. This `plan.md` is the only contract. When ready, say **"do your
review"**; the orchestrator runs the full gate, the Opus reviewers, the wiki sweep, then review →
verdict → merge → retro. **TDD + commit-after-green. Scoped staging. Do NOT write `.scrum/` board state.**

### The six-command DoD gate — exit 0 each
`pytest` · `lint-imports` (**5 kept / 0 broken** — seed is composition wiring; NO new contract) ·
`python scripts/check_fk_direction.py` (stays green — the new FK is spine→spine) ·
`alembic upgrade head` (**does real work this sprint** — the new migration) · `ruff check .` ·
`ruff format --check .`. DB-gated: `scripts/dev_db.py up` → run → `down`.

### Established facts the implementer builds on
- Migration head is `3a8254bcfe59` (spine schema). The new revision sets `down_revision = "3a8254bcfe59"`.
  Generate via `alembic revision -m "add signals.component_id"` (needs `DATABASE_URL_DIRECT` set, since
  `migrations/env.py` resolves the URL at import) OR hand-author the revision file.
- `signals`: `signal_key TEXT PK`, `app_id TEXT FK→apps`, `name`, `created_at`, `updated_at` — NO
  component_id yet. `components`: `id TEXT PK`, `app_id`, `name`, `status TEXT default 'operational'`,
  timestamps. `apps`: `id TEXT PK`, `name`, `config JSONB NOT NULL`, timestamps. Both `signals` and
  `components` are in the `check_fk_direction.py` SPINE allowlist (a signals→components FK is spine→spine
  and is NOT flagged).
- Config layer (STORY-040a, `composition/config.py`): `load_config(config_dir) -> Config` globs
  `config_dir/*.yaml` (point it at `config/apps`); `Config.apps: list[AppConfig]`, each `AppConfig` has
  `id, name, monitor_provider, components: list[ComponentConfig]{id,name}, signals:
  list[SignalConfig]{signal_key,native_id,name,component_id,interval_seconds}, thresholds: AntiFlapThresholds`.
- `create_app` (`composition/app.py`): real branch builds the `Engine` + Postgres repos, sets
  `app.state.db_engine`; injected branch sets `db_engine = None`. The `lifespan` currently disposes the
  engine on shutdown (after `yield`). `composition/settings.py::load_settings` reads `DATABASE_URL`.
- Adapter SQL idiom: `sa.table(...)`/`sa.column(...)` + `sqlalchemy.dialects.postgresql.insert` for
  `ON CONFLICT` (see `proposal_repository.py::create_open`). Engine from the `migrated_db` fixture URL.

---

## STORY-040 — Topology seed + migration + boot wiring (5 pts) — gate + Opus reviewers

No new lint contract. Upserts are `ON CONFLICT DO UPDATE` (not check-then-act → TOCTOU N/A).

### Phase A — migration (TDD-ish; gate-verified)
- [ ] **A1** New Alembic revision (`down_revision = "3a8254bcfe59"`): `op.add_column("signals",
      sa.Column("component_id", sa.Text(), sa.ForeignKey("components.id", ondelete="RESTRICT"),
      nullable=True))` + `op.create_index("ix_signals_component_id", "signals", ["component_id"])`.
      `downgrade` drops the index + column. Verify: `alembic upgrade head` (exit 0),
      `alembic downgrade -1` then `upgrade head` round-trips, `check_fk_direction.py` green.

### Phase B — `seed_topology` (TDD, DB-gated)
- [ ] **B1** Failing DB-gated test (`backend/tests/test_seed.py`, `migrated_db` fixture):
      `seed_topology(config, engine)` from a small in-test `Config` inserts the app(s)/component(s)/
      signal(s); signals carry their `component_id`; `GET`-equivalent reads return them.
- [ ] **B2** Implement `backend/src/composition/seed.py::seed_topology(config: Config, engine: Engine)
      -> None` — upsert in FK order, each in `engine.begin()`:
      - apps: `INSERT (id, name, config) ON CONFLICT (id) DO UPDATE SET name=excluded.name,
        config=excluded.config, updated_at=now()`. `config` = the app's thresholds as JSON
        (`{"thresholds": thresholds.model_dump()}`) — satisfies `apps.config NOT NULL`.
      - components: `INSERT (id, app_id, name) ON CONFLICT (id) DO UPDATE SET name=excluded.name,
        app_id=excluded.app_id, updated_at=now()` — **NOT `status`** (runtime state; new rows take the
        default `operational`).
      - signals: `INSERT (signal_key, app_id, name, component_id) ON CONFLICT (signal_key) DO UPDATE
        SET app_id=…, name=…, component_id=…, updated_at=now()`.
      Composition wiring; docstrings cite §7/§9/§17. Green. Commit.
- [ ] **B3** Failing test → **idempotency (AC2):** run `seed_topology` TWICE on unchanged config →
      identical row counts + values (no duplicates, no churn beyond updated_at). Green.
- [ ] **B4** Failing test → **status preservation (AC3):** seed; `UPDATE components SET
      status='degraded'`; re-seed → the component's `status` is STILL `degraded`. Green.

### Phase C — CLI
- [ ] **C1** `scripts/seed_topology.py` (mirror `scripts/check_fk_direction.py`): `load_config(
      os.environ.get("CONFIG_DIR", "config/apps"))` + build an `Engine` from `DATABASE_URL` (pooled —
      DML) + `seed_topology`; print a short summary; nonzero exit + clear message on a load/validation
      failure (AC5). A DB-gated test (or a subprocess/`main()` call) seeds the throwaway DB and exits 0.

### Phase D — app-startup wiring (TDD, DB-gated)
- [ ] **D1** Add `CONFIG_DIR` to `composition/settings.py` (optional, default `config/apps`).
      `create_app(*, config_dir: str | None = None, …)`: in the REAL branch, after building the engine,
      `app.state.seed_config = load_config(config_dir or settings.config_dir)` (fail-fast — a bad config
      raises at construction); injected branch sets `app.state.seed_config = None`. In the `lifespan`
      STARTUP (before `yield`): `if getattr(app.state, "seed_config", None) is not None and
      app.state.db_engine is not None: seed_topology(app.state.seed_config, app.state.db_engine)`.
      (Existing shutdown engine-dispose stays after `yield`.)
- [ ] **D2** Failing test → **AC4:** with the `migrated_db` engine + a `config_dir` pointing at a tiny
      test config (or `config/apps`), drive `create_app` through its lifespan (`with TestClient(app):`)
      → `GET /api/v1/components` returns the seeded components. Also: a `create_app` with an invalid
      `config_dir` (malformed yaml) fails FAST (raises). Existing fake-injected app tests still pass
      (no engine → no seed). Green.

### Phase E — blast radius + gate
- [ ] **E1** Wiki blast radius via the MECHANICAL sweep (2026-06-28): update/re-verify EVERY stale
      article. Expect `migrations-and-db` (new revision + the signal→component link),
      `config-layer` / `architecture-boundary` / `persistence-adapters` as flagged. Symbol citations;
      bump verified_sha.
- [ ] **E2** Full SIX-command gate green (DB up).

**AC mapping:** AC1 ← A1; AC2 ← B3; AC3 ← B4; AC4 ← D2; AC5 ← C1; AC6 ← E.

---

## Standing conventions checklist (binds all new code)
- [ ] `seed.py` is composition wiring — no domain logic; core untouched; docstrings cite §7/§9/§17.
- [ ] Idempotency, status-preservation, and fail-fast are each tested (AC2/AC3/AC4).
- [ ] DB-gated tests stay green on a REUSED DB: the tests here seed apps/components/signals — clean
      those tables (or rely on the throwaway-DB) so a second suite run passes (STORY-039 truncate only
      covers runtime signal tables; extend cleanup to the topology tables this story seeds).
- [ ] `src` never imports `tests`; no sentinel mappings; scoped staging; mirror existing adapter SQL idiom.
- [ ] Wiki blast radius = the mechanical sweep over ALL articles.

## Notes / risks
- Top-of-range 5 (startup wiring is the extra). If it balloons: migration + `seed_topology` + CLI
  (AC1/AC2/AC3/AC5) is the must-have; the lifespan wiring (AC4) is the stretch — Block rather than guess.
- One new migration; no new tooling/contract.
