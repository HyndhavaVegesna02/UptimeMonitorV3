---
title: Dev setup and the Definition-of-Done gate
code_refs: [pyproject.toml, CLAUDE.md, .scrum/definition-of-done.md, scripts/check_fk_direction.py, scripts/dev_db.py, backend/tests/conftest.py, .gitattributes]
verified_sha: ed19084
verified_sprint: sprint-22
status: verified
---

## Facts (verified against code)
- Python 3.13; setuptools build backend (`pyproject.toml:1-3`). Runtime deps: fastapi,
  pydantic>=2, sqlalchemy>=2, alembic, psycopg[binary], pyyaml, httpx (`pyproject.toml` —
  `[project] dependencies`; pyyaml added sprint-16 STORY-040a for the config loader, httpx
  promoted to a runtime dep sprint-20 STORY-016 for the Grail + Statuspage HTTP executors).
  Dev extras: pytest, import-linter, ruff (`pyproject.toml` — `[project.optional-dependencies] dev`).
- Setup: `python -m venv .venv` then `.venv/Scripts/python.exe -m pip install -e ".[dev]"`
  (Windows; call `.venv` binaries directly). Documented in `CLAUDE.md` "Key commands".
- pytest is configured with `testpaths = ["backend/tests"]` (`pyproject.toml:27-28`).
- **The DoD gate is six bare commands**, each must exit 0 (`.scrum/definition-of-done.md`):
  1. `pytest`
  2. `lint-imports` (5 import-linter contracts; the 4th, `api-feature-independence`, added STORY-014; the 5th, `src-no-tests`, added STORY-038 to forbid `src` importing `tests`)
  3. `python scripts/check_fk_direction.py` (needs `DATABASE_URL` → migrated Postgres)
  4. `alembic upgrade head` (needs `DATABASE_URL_DIRECT`)
  5. `ruff check .`
  6. `ruff format --check .`
  All six are live as of STORY-033. Commands 2–4 became real during Sprint 0 (bootstrap); commands 5 and 6 were added in Sprint 11.
  - `[tool.ruff]` carries `exclude = [".agents", ".venv"]` (`pyproject.toml`, STORY-016c): `.agents/` is
    untracked third-party skills tooling (not project code) that otherwise makes `ruff check .` /
    `ruff format --check .` exit non-zero; the exclude scopes ruff to project code without affecting
    `backend/`/`migrations/`. `.venv` is already gitignored and conventionally skipped — listed for
    defensiveness.
- **Standard way to obtain a migrated throwaway DB (STORY-019):**
  `scripts/dev_db.py` — `python scripts/dev_db.py up` starts a throwaway
  `postgres:16`, waits for `pg_isready`, runs `alembic upgrade head`, and
  prints `DATABASE_URL` (plain libpq) + `DATABASE_URL_DIRECT` (`+psycopg`);
  `python scripts/dev_db.py down` removes the container. This replaces
  hand-rolling commands 3 & 4's setup (the manual `docker run` one-liner below
  is now a documented fallback, not the standard path).
  `python scripts/dev_db.py up` is idempotent: it force-removes any pre-existing
  container of the same name before attempting `docker run`, so a leftover/stuck
  container no longer blocks startup (STORY-030).
- Under `pytest`, the same logic is the session-scoped `migrated_db` fixture
  (`backend/tests/conftest.py`, via `dev_db.resolve_db()`): reuses
  `DATABASE_URL`/`DATABASE_URL_DIRECT` if both are already set externally
  (migrating to ensure current, no container spawned); else spawns a
  throwaway `postgres:16` on a free port if Docker is available (PID+UUID
  -unique container name, to avoid collisions between nested/concurrent
  pytest runs), tearing it down in a `finally`-block finalizer that runs even
  if a test fails; else skips the DB-gated tests cleanly (no error). DB-gated
  tests (e.g. `backend/tests/test_spine_schema.py`) depend on this fixture
  instead of each rolling its own `skipif` + connection setup. A function-scoped
  `clean_runtime_tables` fixture (STORY-039) truncates the runtime tables before
  each DB-gated test, so the suite passes even against a reused, already-populated
  DB (the session-scoped DB is shared; per-test isolation comes from the truncate).
- Manual fallback one-liner for commands 3 & 4 (Docker 28.x), if not using
  `scripts/dev_db.py`:
  `docker run -d --name uptime_pg_test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=uptime -p 55432:5432 postgres:16`
  (full one-liner + env exports in `CLAUDE.md` "Database & migrations").
- The console script is `lint-imports` (`.venv/Scripts/lint-imports.exe`); `python -m importlinter`
  does NOT work (it is a package with no `__main__`). **Gotcha (operational):** the `.exe` launcher
  occasionally fails to start with `Permission denied` / `ApplicationFailed` (a corrupted/locked
  Windows launcher, not a contract break). Regenerate it with
  `.venv/Scripts/python.exe -m pip install --force-reinstall --no-deps import-linter` and re-run;
  to confirm the contracts independently of the launcher,
  `.venv/Scripts/python.exe -c "import sys; from importlinter.cli import lint_imports; sys.exit(lint_imports())"`.
- No `psql` client installed. Neon/Dynatrace/Statuspage credentials were not needed through the
  pure-backend sprints; the live loop (`python -m src.composition.run`, STORY-016) reads four secrets
  from the environment / a gitignored `.env` (`DYNATRACE_ENV_URL`, `DYNATRACE_API_TOKEN`,
  `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY` — see CLAUDE.md "Live-loop secrets"). They are NOT part
  of the six-command DoD gate (every test uses recorded fixtures).
- **Line endings are normalized to LF in the repo** via `.gitattributes` (`* text=auto eol=lf`
  + `binary` rules for `*.png/jpg/jpeg/gif/ico/pdf/woff/woff2`; STORY-018). Gotcha: the index
  blobs were already LF, so `git add --renormalize .` stages nothing — the CRLF a Windows
  checkout shows in the *working tree* comes from the contributor's global `core.autocrlf=true`
  (a checkout-time conversion), not from repo content. `.gitattributes` keeps it that way and
  stops the per-commit `LF will be replaced by CRLF` warnings.

## Inference (synthesis, not verified)
- `.scrum/definition-of-done.md` is the single canonical DoD (Sprint 0 retro working
  agreement, 2026-06-23). The root `definition-of-done.md` is now just a one-line pointer to
  it — no second editable copy.

## History
- sprint-0: created (compile pass folding STORY-001/002/003 setup learnings).
- sprint-3: updated (STORY-019 shared throwaway-DB harness) — added the
  `scripts/dev_db.py` CLI (`up`/`down`) as the standard way to obtain a
  migrated DB for commands 3 & 4, and the `migrated_db` pytest session
  fixture's reuse/spawn/skip decision logic; the prior hand-rolled `docker run`
  one-liner is now documented as a fallback, not the standard path.
  `verified_sha` re-stamped accordingly.
- sprint-10: updated to note the idempotency behavior of `dev_db.py up` (STORY-030).
- sprint-12: STORY-014 added the 4th `lint-imports` contract (`api-feature-independence`); the
  `lint-imports` command now enforces 4 contracts. Re-verified at eb147ef.
  Verified at 70622a1.
- sprint-11: updated to note the ruff lint and format check integration in the DoD gate (STORY-033).
  Verified at d557749.
- sprint-14: STORY-038 added the 5th `lint-imports` contract (`src-no-tests`, forbidden: `src` may not import `tests`) to prevent production code importing fakes/mocks. The `lint-imports` command now enforces 5 contracts. Re-verified at fafdc4c.
- sprint-16: STORY-040a added `pyyaml` to `[project.dependencies]` (runtime dep for the config-layer loader). Runtime-deps Fact updated; no contract or DoD command changed. Re-verified at 9b60fac.
- sprint-20: STORY-016 promoted `httpx` from a dev extra to a runtime dep (Grail + Statuspage HTTP
  executors) and removed a stray `httpx2`; added the `python -m src.composition.run` live-loop command
  + its four env secrets to CLAUDE.md. No contract or DoD command changed (still six). Re-verified at d9c2a77.
- sprint-22: STORY-016c added `[tool.ruff] exclude = [".agents", ".venv"]` so `ruff check .` /
  `ruff format --check .` stay green against untracked third-party skills tooling under `.agents/`
  (84 ruff errors there, none in project code). No contract or DoD command changed (still six).
  Re-verified at ed19084.
