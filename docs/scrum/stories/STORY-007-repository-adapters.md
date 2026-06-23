---
id: STORY-007
title: Repository adapters behind the ports
type: feature
---

## Context
Spec: dossier §6 (repository ports) + §9 (schema). Zone 2. Neon-backed implementations
of the repository ports from STORY-005. All SQL stays behind the repository layer.

## Description
Implement the repository ports in `adapters/persistence/` (Neon/Postgres via
SQLAlchemy). `save_new` uses `INSERT … ON CONFLICT (source_event_id) DO NOTHING`;
the watermark repository is core-owned in semantics but DB-backed here. No SQL leaks
above the repository layer.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Each repository adapter implements its port interface from STORY-005.
- [ ] AC2: Integration tests run against a test database (Dockerized Postgres) and cover
      insert/idempotency/read paths.
- [ ] AC3: No SQL appears above the repository layer (enforced by review + `lint-imports`:
      `sqlalchemy` forbidden in `core`).
- [ ] AC4: `ON CONFLICT DO NOTHING` idempotency proven by a duplicate-insert test.

## Open Questions
- Confirm which repositories are in scope for this story vs deferred.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §6/§9. Status: draft — refine before its sprint.
