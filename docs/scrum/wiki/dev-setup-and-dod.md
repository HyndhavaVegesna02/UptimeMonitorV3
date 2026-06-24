---
title: Dev setup and the Definition-of-Done gate
code_refs: [pyproject.toml, CLAUDE.md, .scrum/definition-of-done.md, scripts/check_fk_direction.py, .gitattributes]
verified_sha: 6128cb0
verified_sprint: sprint-2
status: verified
---

## Facts (verified against code)
- Python 3.13; setuptools build backend (`pyproject.toml:1-3`). Runtime deps: fastapi,
  pydantic>=2, sqlalchemy>=2, alembic, psycopg[binary] (`pyproject.toml:10-16`). Dev extras:
  pytest, import-linter (`pyproject.toml:18-19`).
- Setup: `python -m venv .venv` then `.venv/Scripts/python.exe -m pip install -e ".[dev]"`
  (Windows; call `.venv` binaries directly). Documented in `CLAUDE.md` "Key commands".
- pytest is configured with `testpaths = ["backend/tests"]` (`pyproject.toml:27-28`).
- **The DoD gate is four bare commands**, each must exit 0 (`.scrum/definition-of-done.md`):
  1. `pytest`
  2. `lint-imports` (3 import-linter contracts)
  3. `python scripts/check_fk_direction.py` (needs `DATABASE_URL` → migrated Postgres)
  4. `alembic upgrade head` (needs `DATABASE_URL_DIRECT`)
  All four are live as of STORY-003. Commands 2–4 became real during Sprint 0 (bootstrap).
- Throwaway Postgres for commands 3 & 4 (Docker 28.x):
  `docker run -d --name uptime_pg_test -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=uptime -p 55432:5432 postgres:16`
  (full one-liner + env exports in `CLAUDE.md` "Database & migrations").
- The console script is `lint-imports` (`.venv/Scripts/lint-imports.exe`); `python -m importlinter`
  does NOT work (it is a package with no `__main__`).
- No `psql` client installed; no Neon/Dynatrace/Statuspage credentials needed in Sprint 0.
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
