---
id: STORY-087
title: Composition cutover to DynamoDB — retire Postgres, DoD amendment takes effect
type: chore
---

## Context
AWS migration epic (see STORY-082 Context). The flip: both processes
(`composition/app.py`, `composition/run.py`) wire the DynamoDB adapters
(STORY-083..086) and the Postgres path is deleted. **This is the story where the
PO-approved DoD amendment (2026-07-14) takes effect:** `alembic upgrade head` and
`python scripts/check_fk_direction.py` retire from the gate; the DynamoDB-Local-backed
pytest suite carries the persistence floor (and `cfn-lint infra/` joins at STORY-088).
Fresh-start cutover per PO decision — no Neon data migrates; topology reseeds from
config, observations regenerate from Dynatrace, watermarks re-establish on first cycle.

Deletion reasons must be recorded (DoD standing rule): Postgres adapters, Alembic tree,
`scripts/dev_db.py`, `scripts/check_fk_direction.py`, `migrated_db` fixture, and the
two-URL (`DATABASE_URL`/`DATABASE_URL_DIRECT`) machinery — all superseded by the
DynamoDB persistence zone. Their tombstones feed the wiki archive.

## Description
Wire DynamoDB adapters in both composition roots; drop SQLAlchemy/Alembic/psycopg from
runtime; amend `.scrum/definition-of-done.md` and CLAUDE.md; resolve the wiki blast
radius (persistence/schema/dev-db articles).

## Acceptance Criteria
- [ ] AC1 (wiring): `create_app()` and `run.py::main()` construct DynamoDB adapters
      from settings (region/table names); no `sqlalchemy.create_engine` remains under
      `backend/src`; the API and the live loop start and serve with only
      `AWS_REGION`/table-name/secret env vars (a repo-root `.env` still loads for local
      dev per STORY-043, and exported vars still win).
- [ ] AC2 (retirement): Postgres adapters, `alembic.ini` + `migrations/`,
      `scripts/dev_db.py`, `scripts/check_fk_direction.py`, and the `migrated_db`
      fixture are deleted with reasons recorded; SQLAlchemy, Alembic, and psycopg leave
      `pyproject.toml` dependencies.
- [ ] AC3 (DoD amendment lands): `.scrum/definition-of-done.md` drops the two retired
      gates and records the DynamoDB-Local pytest floor (PO approval 2026-07-14 cited);
      `python .claude/skills/yourteam/scripts/yt_gate.py` runs GREEN under the amended
      command set on a clean tree.
- [ ] AC4 (e2e proof): the full local stack recipe (DynamoDB Local + uvicorn + live
      loop + frontend dev server) runs the end-to-end thread — loop ingests, watermark
      advances across two cycles, all six tabs render, one mutation round-trips —
      evidence recorded.
- [ ] AC5 (docs): CLAUDE.md's Key commands / Database sections rewritten for DynamoDB
      (create_tables.py, dynamo_local fixture, env var table) in the same story; wiki
      blast radius resolved (stale persistence articles updated or archived with
      tombstones).

## Open Questions
None.

## History
- 2026-07-14: drafted at AWS-migration refinement. Status: draft, 3 points proposed.
- 2026-07-14: PO approved AC + estimate ("approve all") → ready.
