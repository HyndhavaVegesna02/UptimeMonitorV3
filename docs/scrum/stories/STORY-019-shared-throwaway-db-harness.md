---
id: STORY-019
title: Shared throwaway-DB test harness (script + pytest fixture)
type: chore
---

## Context
From the Sprint 2 retro. The two DB-backed DoD gates (`alembic upgrade head`,
`scripts/check_fk_direction.py`) and the DB-gated tests require a migrated throwaway
Postgres. Across Sprint 2 that setup was hand-rolled **five** separate times — each
re-implementing `docker run` + wait-ready + `alembic upgrade head` + the two-URL dialect
split (`DATABASE_URL` plain libpq vs `DATABASE_URL_DIRECT` `+psycopg`). Today
`backend/tests/test_spine_schema.py` carries its own `pytest.mark.skipif(not DATABASE_URL)`
+ a `conn` fixture and assumes a human/CI already migrated the DB. Every remaining Zone 2–4
story is DB-heavy, so the cost and the foot-gun surface (wrong dialect; forgetting to migrate
before the FK check) compound. One shared harness removes it.

Refined 2026-06-24. Decisions locked (resolving the prior open questions):
1. **Python, not bash/PowerShell.** A small `scripts/dev_db.py` helper + a pytest
   **session-scoped fixture** in `backend/tests/conftest.py`. Cross-platform, fits the Python
   stack, and avoids a bash-vs-PowerShell split on a Windows-first repo that nonetheless drives
   the gates from Git Bash.
2. **Fixture behavior:** session-scoped; if `DATABASE_URL`/`DATABASE_URL_DIRECT` are already set
   externally (CI or a running DB), reuse them and ensure the DB is migrated; otherwise, if
   Docker is available, spawn `postgres:16`, wait ready, set both URLs in their correct
   dialects, `alembic upgrade head`, yield, then tear the container down in a finalizer that
   runs **even on test failure**. When neither an external DB nor Docker is available, skip
   cleanly.

## Description
- **Helper** `scripts/dev_db.py` with `up`/`down` (names confirmed at implementation): `up`
  starts a throwaway `postgres:16`, waits ready, runs `alembic upgrade head`, and emits both
  URLs in their correct dialects; `down` removes the container. Replaces the hand-copied
  CLAUDE.md one-liner for manual gate runs.
- **Pytest session fixture** in the existing `conftest.py` implementing the behavior above.
  Migrate `test_spine_schema.py` to depend on it (drop its local `skipif`/`conn` boilerplate),
  proving the fixture on a real consumer. `test_fk_direction.py` stays a pure unit test (no DB)
  — do not touch it.
- Test/dev tooling only — **no production code changes**.

## Acceptance Criteria
- [ ] AC1: `python scripts/dev_db.py up` starts a throwaway `postgres:16`, waits for readiness,
      runs `alembic upgrade head`, and emits `DATABASE_URL` (plain libpq) + `DATABASE_URL_DIRECT`
      (`+psycopg`); afterward `python scripts/check_fk_direction.py` exits 0 with no manual URL
      juggling, and `python scripts/dev_db.py down` removes the container.
- [ ] AC2: A pytest session-scoped fixture supplies a migrated DB to the DB-gated tests;
      `test_spine_schema.py` is refactored onto it (its local `skipif`/`conn` removed) and its
      tests pass through the fixture. The container is torn down even when a test fails (proven
      by a finalizer, not by happy-path cleanup).
- [ ] AC3: With `DATABASE_URL`/`DATABASE_URL_DIRECT` set externally, the fixture reuses them
      (ensuring migrated) and spawns no container; with neither an external DB nor Docker
      available, the DB-gated tests skip cleanly (no error).
- [ ] AC4: `CLAUDE.md` updated to document `scripts/dev_db.py` as the standard local way to run
      the DB gates (command-sync working agreement); the hand one-liner section points to it.
- [ ] AC5: All four DoD gates exit 0 (`pytest`, `lint-imports`, `scripts/check_fk_direction.py`,
      `alembic upgrade head`).

## Open Questions
_(none — ready)_

## History
- 2026-06-24: created from Sprint 2 retro (PO-approved amendment).
- 2026-06-24: refined with PO. Decisions: Python helper + session fixture (not bash/PowerShell);
  reuse-external-or-spawn behavior with teardown-on-failure; refactor `test_spine_schema.py`
  onto the fixture. Estimate held at 3. Status: ready. Planned for Sprint 3 ahead of STORY-007.
- 2026-06-24: implemented (`scripts/dev_db.py` + `migrated_db` session fixture). Spec review PASS
  (5/5 AC). Quality review raised 1 MAJOR (spawn-time container leak: `resolve_db()` could raise
  after `start_container` but before the fixture finalizer registered, leaking the container) +
  the spec reviewer flagged a flaky teardown test (nested-pytest-subprocess raced ~1/4 runs).
  Fix loop 1: guarded the spawn path (`try/except BaseException -> stop_container -> raise`) with a
  regression test, and made the teardown test deterministic via a `provide_migrated_db()` generator
  driven by `.throw()` (no subprocess, no temp file). Recovered across two implementer
  connection-drop crashes; finished by a fresh implementer. Quality re-review APPROVE; DoD green
  (alembic, pytest 84 / 5x consecutive, lint 3 kept, FK 10/0 @ 0a6dd27). Board: done.
  Quality-review MINOR notes (non-blocking, no change required): (1) `_docker_unavailable()` runs
  `docker version` at collection time via the `skipif` decorator arg; (2) earlier-fixed minors —
  string type-annotations on `resolve_db`, fixed-port asymmetry.
