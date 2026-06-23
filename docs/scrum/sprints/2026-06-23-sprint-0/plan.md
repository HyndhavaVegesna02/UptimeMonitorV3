# Sprint 0 — Plan

**Goal:** A running backend skeleton with the four CI contracts green on an empty build —
the boundary gates exist before any business logic.

**Branch:** `sprint-0` (from `main` @ `aa6b3b4`) · **Start tag:** `sprint-0-start`
**Committed:** 8 points (STORY-001 ·3, STORY-002 ·3, STORY-003 ·2). No velocity history →
deliberately under-committed (setup-only).

**Execution order & reasoning:**
1. **STORY-001** first — it creates the package structure the other two depend on.
2. **STORY-002** next — the import-linter contracts + FK-direction check reference the
   zones STORY-001 creates; highest blast radius (it IS the DoD floor), so early.
3. **STORY-003** last — Alembic + the empty baseline migration; the FK-direction check
   (STORY-002) needs a migrated DB to run meaningfully, so the migration scaffold follows.

**Environment for the gate:** Python 3.13.9, Docker 28.5.2 (throwaway Postgres for
`alembic upgrade head` and the FK-direction check). No Neon/Dynatrace/Statuspage creds
needed in Sprint 0.

---

## STORY-001 — Repo scaffold + four-zone structure (3 pts, full pipeline)

- [x] 1. Create `pyproject.toml` (project + deps + `package-dir = {"" = "backend"}` so
      `src` is importable) and a `.venv`; write a failing smoke test
      `backend/tests/test_smoke.py` that imports `src.core` etc. (fails: packages absent).
- [x] 2. Create the four zones with `__init__.py`: `core/{domain,ports,services}`,
      `adapters/{inbound,outbound,persistence}`, `composition`, `api`. Run smoke test → pass. Commit.
- [x] 3. Configure pytest (pythonpath/packaging) so `pytest` exits 0 on the harness;
      confirm `python -c "import src.core, src.adapters, src.composition, src.api"`. Commit.
- [x] 4. Write `CLAUDE.md` (overview, stack, key commands, tooling inventory, YourTeam
      session-start pointer) and `config/README` placeholder. Commit.
- [x] 5. Self-run DoD (`pytest` → 0); self-review diff. Report.

## STORY-002 — CI contracts = the DoD floor (3 pts, full pipeline)

- [x] 1. Add import-linter config (pyproject `[tool.importlinter]` or `.importlinter`):
      contract `core-independence` (forbidden). Write a test/demonstration that a forbidden
      import makes `lint-imports` fail, then ensure the clean skeleton passes. Commit.
- [x] 2. Add `core-internal-layering` (layers: services→ports→domain) and
      `adapters-dont-cross` (independence) contracts; `lint-imports` → 0 on skeleton. Commit.
- [x] 3. Write failing unit test for `scripts/check_fk_direction.py` violation logic
      (fake FK set incl. a spine→feature edge → flagged). Commit test.
- [x] 4. Implement `scripts/check_fk_direction.py` (reads `information_schema` via
      `DATABASE_URL`, §9 SPINE allowlist, direction-only); unit test passes. Commit.
- [x] 5. Run it against a migrated empty DB (Dockerized Postgres) → exit 0 (zero FKs);
      confirm both commands are the bare DoD commands. Commit.
- [x] 6. Self-run DoD (`pytest`, `lint-imports`, `check_fk_direction.py` → all 0); report.

## STORY-003 — Alembic + Neon two-connection setup (2 pts, light pipeline)

- [x] 1. `alembic init` at repo top level; configure `env.py` to read
      `DATABASE_URL_DIRECT` for migrations; app settings read `DATABASE_URL` (pooled).
      Write a test/asserts the two vars are wired distinctly. Commit.
- [x] 2. Create the empty baseline migration (real `upgrade`/`downgrade`, no tables, no
      `create_all`). Commit.
- [x] 3. Bring up throwaway Postgres (documented one-liner); `alembic upgrade head` → 0;
      `alembic downgrade base` → `alembic upgrade head` round-trips → 0. Commit.
- [x] 4. Update `CLAUDE.md` with migration command + connection-var convention + the
      Postgres one-liner. Commit.
- [ ] 5. Self-run full DoD (`pytest`, `lint-imports`, `check_fk_direction.py`,
      `alembic upgrade head` → all 0); report.

---

## Sprint-end (before review)
- Wiki compile pass (seed initial verified articles for the scaffold/boundary if useful).
- Prepare `review.md`: per-story AC checklist with DoD evidence; demo the green contracts.
