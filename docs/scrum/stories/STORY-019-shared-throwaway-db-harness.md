---
id: STORY-019
title: Shared throwaway-DB test harness (script + pytest fixture)
type: chore
---

## Context
From the Sprint 2 retro. The two DB-backed DoD gates (`alembic upgrade head`,
`scripts/check_fk_direction.py`) and the DB-gated tests require a migrated throwaway
Postgres. Across Sprint 2, that setup was hand-rolled **five** separate times
(STORY-006 implementer, spec reviewer, the orchestrator DoD gate, STORY-018 implementer,
its gate) — each re-implementing `docker run` + wait-ready + `alembic upgrade head` + the
two-URL dialect split (`DATABASE_URL` plain libpq vs `DATABASE_URL_DIRECT` `+psycopg`).
Every remaining Zone 2–4 story is DB-heavy, so the cost and the foot-gun surface (wrong
dialect, forgetting to migrate before the FK check) compound. One shared harness removes it.

## Description
Provide a single reusable way to obtain a migrated throwaway Postgres:
- A **helper** (e.g. `scripts/dev_db.*` or a documented runner target) that starts a
  throwaway `postgres:16`, waits until ready, runs `alembic upgrade head`, and exports both
  connection URLs in their correct dialects.
- A **pytest session-scoped fixture** that DB-gated tests depend on, so they stop carrying
  their own skip/connect boilerplate. It must reuse an externally-provided `DATABASE_URL`
  when present (CI / a running DB) and otherwise manage a container locally, with teardown
  that runs even on test failure.

No production code changes — this is test/dev tooling only.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: One command/helper starts a throwaway `postgres:16`, waits for readiness, runs
      `alembic upgrade head`, and emits `DATABASE_URL` (plain) + `DATABASE_URL_DIRECT`
      (`+psycopg`); after running it, `python scripts/check_fk_direction.py` exits 0 with no
      manual URL juggling.
- [ ] AC2: A pytest session-scoped fixture supplies a migrated DB to the existing DB-gated
      tests (`backend/tests/test_spine_schema.py`, `test_fk_direction.py`); they pass through
      the fixture and the container is torn down even when a test fails.
- [ ] AC3: The fixture reuses an externally-set `DATABASE_URL` when present (no container
      spawned), and skips cleanly when neither an external DB nor Docker is available.
- [ ] AC4: `CLAUDE.md` updated to document the harness as the standard way to run the DB
      gates locally (command-sync working agreement).
- [ ] AC5: All four DoD gates exit 0.

## Open Questions
- Bash script vs PowerShell vs a tiny Python runner for the helper (Windows-first repo).
- Exact fixture scope/teardown semantics and the CI-vs-local reuse switch — confirm at refinement.
- Sequencing: planning should consider running this BEFORE STORY-007 so the repository
  adapters' integration tests are written against the fixture from the start.

## History
- 2026-06-24: created from Sprint 2 retro (PO-approved amendment). Status: draft — refine
  and estimate before a sprint. Provisional estimate 3 (Docker lifecycle in a fixture +
  CI/local reuse + teardown-on-failure + doc sync).
