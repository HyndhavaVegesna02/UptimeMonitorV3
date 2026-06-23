---
id: STORY-003
title: Alembic + Neon two-connection setup
type: chore
---

## Context
Spec: `uptime-monitor-v3-design.html` §3 (Neon pooled vs direct connection strings),
§4 ("real Alembic migrations live at the repository top level, versioned from day one
— never `create_all`"), and §17 (migrations run as a separate release step using the
DIRECT connection; app runtime uses the POOLED connection). V2's flagged gap was an
empty `versions/` + `create_all`; this story closes it from day one.

## Description
Initialize Alembic at the repository top level (migrations are not buried inside
`backend/`). Establish the two-connection split:
- **Migrations** use `DATABASE_URL_DIRECT` (the non-pooled/direct connection — DDL
  misbehaves through PgBouncer transaction pooling).
- **App config** reads `DATABASE_URL` (the pooled connection) for runtime.

Create an empty baseline migration (`upgrade`/`downgrade` present, no tables — the
spine schema arrives in STORY-006) that applies cleanly to a fresh database. For
Sprint 0 / CI there is no Neon yet: run against a throwaway Postgres
(`docker run -e POSTGRES_PASSWORD=... -p 5432:5432 postgres:16`), with
`DATABASE_URL_DIRECT` pointed at it. Document the one-command way to bring that DB up
and run the migration so the DoD's `alembic upgrade head` is reproducible. Update
`CLAUDE.md` with the migration command and the connection-variable convention.

Do NOT define any spine tables here and never introduce `create_all` anywhere.

## Acceptance Criteria
- [ ] AC1: `alembic upgrade head` exits 0 against a fresh, empty database (the
      throwaway Postgres), applying the empty baseline migration.
- [ ] AC2: The migration path reads `DATABASE_URL_DIRECT`; the application config reads
      `DATABASE_URL` (pooled). The two are wired to distinct env vars and this split is
      visible in code (Alembic env.py uses DIRECT; app settings use pooled).
- [ ] AC3: Alembic is initialized at the repo top level with a real `versions/`
      directory containing the baseline revision (no empty `versions/`, no `create_all`).
- [ ] AC4: `alembic downgrade base` then `alembic upgrade head` round-trips cleanly
      (the baseline migration is reversible), exit 0 both ways.
- [ ] AC5: `CLAUDE.md` documents the migration command and the
      `DATABASE_URL` / `DATABASE_URL_DIRECT` convention, plus the one-liner to start the
      throwaway Postgres for local/CI runs.

## Open Questions
<!-- none — ready. Sprint 0 uses a Dockerized Postgres for the gate; real Neon DIRECT
     connection is wired in the deployment zone (STORY-017). -->

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §3/§4/§17; refined to ready for Sprint 0.
  Confirmed Docker 28.5.2 is available locally, so the `alembic upgrade head` gate runs
  against a throwaway Postgres container (no Neon credentials needed for Sprint 0).
