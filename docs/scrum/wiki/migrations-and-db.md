---
title: Migrations and the two-connection database split
code_refs: [alembic.ini, migrations/, backend/src/composition/settings.py]
verified_sha: 2ee3266
verified_sprint: sprint-0
status: verified
---

## Facts (verified against code)
- Alembic is initialized at the **repo top level** (dossier §4): `alembic.ini` + `migrations/`
  (with `env.py`, `versions/`, `script.py.mako`) — NOT under `backend/`.
- The baseline migration is `migrations/versions/eda70ac11454_baseline.py` — a real revision
  with `upgrade()`/`downgrade()` that creates NO tables (spine schema arrives in STORY-006).
  It is reversible: `downgrade base` → `upgrade head` round-trips to exit 0.
- **No `create_all` anywhere** — every table must arrive via an explicit migration. The only
  textual occurrences of `create_all` are comments in the baseline file forbidding it.
- **Two distinct connection env vars, never mixed** (dossier §3, §17):
  - `DATABASE_URL` — Neon **pooled** (PgBouncer); read by app runtime
    (`backend/src/composition/settings.py:20,36`, const `APP_DATABASE_URL_VAR`) and by
    `scripts/check_fk_direction.py` (`:85`).
  - `DATABASE_URL_DIRECT` — Neon **direct** (non-pooled); read by Alembic
    (`migrations/env.py`). DDL misbehaves through transaction pooling, so migrations run as a
    separate release step on the direct connection.
- App config / env-var reading lives in the **composition** zone
  (`backend/src/composition/settings.py`), never in `core/` — the import-linter boundary
  forbids core importing infrastructure. `load_settings()` raises `KeyError` if `DATABASE_URL`
  is unset (the app must not start without a DB URL).
- **URL dialect split (gotcha):** Alembic (SQLAlchemy 2) needs the psycopg3 dialect
  `postgresql+psycopg://…` (env.py normalizes to it); `scripts/check_fk_direction.py` uses
  raw psycopg and needs the plain libpq form `postgresql://…` (the `+psycopg` prefix makes
  raw psycopg raise). So against the same DB, set `DATABASE_URL_DIRECT` to the `+psycopg`
  form and `DATABASE_URL` to the plain form. (Documented in `CLAUDE.md`.)
- Sprint-0 / CI runs against a throwaway Dockerized `postgres:16` (host port 55432); real
  Neon connection strings are deferred to the deployment zone (STORY-017).

## Inference (synthesis, not verified)
- `migrations/env.py` resolves the URL at import time, so any `alembic` subcommand (even
  `revision`) currently requires `DATABASE_URL_DIRECT` set — flagged as a possible ergonomics
  tweak later (see STORY-003 History).

## History
- sprint-0: created (STORY-003 Alembic + two-connection setup).
