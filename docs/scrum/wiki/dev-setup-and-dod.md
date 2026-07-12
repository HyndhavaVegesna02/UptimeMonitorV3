---
title: Dev setup and the Definition-of-Done gate
code_refs: [pyproject.toml, CLAUDE.md, .scrum/definition-of-done.md, scripts/check_fk_direction.py, scripts/dev_db.py, backend/tests/conftest.py, .gitattributes, frontend/package.json, backend/src/composition/asgi.py, backend/src/composition/run.py, backend/tests/test_spine_schema.py]
verified_sha: 678ff0d
verified_sprint: sprint-44
status: verified
---

## Facts (verified against code)
- Python 3.13; setuptools build backend (`pyproject.toml:1-3`). Runtime deps: fastapi,
  pydantic>=2, sqlalchemy>=2, alembic, psycopg[binary], pyyaml, httpx, python-dotenv
  (`pyproject.toml` — `[project] dependencies`; pyyaml added sprint-16 STORY-040a for the config
  loader, httpx promoted to a runtime dep sprint-20 STORY-016 for the Grail + Statuspage HTTP
  executors, python-dotenv added sprint-36 STORY-043 so the two process entrypoints can load a
  `.env` file). Dev extras: pytest, import-linter, ruff, uvicorn[standard] (`pyproject.toml` —
  `[project.optional-dependencies] dev`; `uvicorn` added sprint-28 STORY-042 as the local ASGI dev
  server — see "Run the app locally" below).
- Setup: `python -m venv .venv` then `.venv/Scripts/python.exe -m pip install -e ".[dev]"`
  (Windows; call `.venv` binaries directly). Documented in `CLAUDE.md` "Key commands".
- pytest is configured with `testpaths = ["backend/tests"]` (`pyproject.toml:27-28`).
- **The DoD gate is six bare commands**, each must exit 0 (`.scrum/definition-of-done.md`):
  1. `pytest`
  2. `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"`
     (2026-07-12, sprint-44: invocation moved OFF the `lint-imports` exe shim — a Windows
     Application Control policy now blocks it on this machine; same 5 import-linter contracts,
     same check, module-path invocation instead; the 4th contract, `api-feature-independence`,
     added STORY-014; the 5th, `src-no-tests`, added STORY-038 to forbid `src` importing `tests`)
  3. `python scripts/check_fk_direction.py` (needs `DATABASE_URL` → migrated Postgres)
  4. `alembic upgrade head` (needs `DATABASE_URL_DIRECT`)
  5. `ruff check .`
  6. `ruff format --check .`
  All six are live as of STORY-033. Commands 2–4 became real during Sprint 0 (bootstrap); commands 5 and 6 were added in Sprint 11.
  - `[tool.ruff]` carries `exclude = [".agents", ".venv", "frontend"]` (`pyproject.toml`; `.agents`
    STORY-016c, `frontend` STORY-015a): `.agents/` is untracked third-party skills tooling that otherwise
    makes `ruff check .` / `ruff format --check .` exit non-zero; `frontend/` is the JS/TS SPA (no Python)
    excluded so the Python formatter/linter stays scoped to backend code. `.venv` is already gitignored
    and conventionally skipped — listed for defensiveness.
- **The frontend has its own three-command DoD gate (live as of STORY-015a, sprint-25), run from
  `frontend/`** (`.scrum/definition-of-done.md` "Commands (frontend)"; commands in `frontend/package.json`):
  1. `npm test` — Vitest run-once (`"test": "vitest run"`)
  2. `npm run build` — `tsc -b && vite build` (the type-check is part of the build gate)
  3. `npm run lint` — ESLint flat config (`eslint .`)
  These are INDEPENDENT of the six backend commands: the frontend is isolated (no backend import, no
  shared build step), so a backend-only story never runs the npm gates and a frontend-only story never
  runs the six backend commands. The `.scrum/definition-of-done.md` frontend section stopped being a
  "placeholder until then" note and became live in the same commit (`08d91e7`) that documented the
  commands + `frontend/` layout in CLAUDE.md (command-sync agreement). Toolchain: Vite + React +
  TypeScript (strict), Vitest + React Testing Library + MSW (the only mocked I/O edge in frontend tests),
  npm on Node 24. Playwright/E2E is deferred to a later integration story.
- **Running the app locally (STORY-042; `.env` loading STORY-043):** the FastAPI API is served via
  the ASGI entrypoint `backend/src/composition/asgi.py` (`app = create_app()` — reads `DATABASE_URL`
  + the topology config, default `config/apps`, so the boot-time seed runs), launched with
  `uvicorn src.composition.asgi:app --port 8000`. The Vite dev proxy (`/api` → `:8000`) then reaches it.
  Full local stack (CLAUDE.md "Run the app locally"): `dev_db.py up` → export `DATABASE_URL` (or place
  it in a repo-root `.env` — see the STORY-043 correction above) → the uvicorn command → a 2nd terminal
  running the live loop `python -m src.composition.run` (populates proposals/observations/publications)
  → `npm run dev`. Two processes share one `DATABASE_URL`; no CORS locally (same-origin via the proxy —
  real CORS is STORY-017). Before STORY-042 the API had only ever run in-process via `TestClient` (no
  ASGI server, no module-level app).
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
  Container readiness timeout is tunable via the `DEV_DB_READY_TIMEOUT_SECONDS`
  environment variable (defaults to `60.0` seconds), which leverages a patient
  retry/backoff loop with a 5-second bounded exec timeout under concurrent load
  (STORY-073).
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
  does NOT work (it is a package with no `__main__`). **Gotcha (operational, superseded
  2026-07-12):** the `.exe` launcher used to occasionally fail with `Permission denied` /
  `ApplicationFailed` (a corrupted/locked Windows launcher); the fix was to regenerate it via
  `.venv/Scripts/python.exe -m pip install --force-reinstall --no-deps import-linter`, or confirm
  the contracts independently of the launcher via
  `.venv/Scripts/python.exe -c "import sys; from importlinter.cli import lint_imports; sys.exit(lint_imports())"`.
  **This module-path form is now the STANDING DoD command #2** (sprint-44 gate hygiene fix): a
  Windows Application Control policy started blocking the `.exe` shim outright (not merely a
  corrupted-launcher flake), so `CLAUDE.md` and `.scrum/definition-of-done.md` were updated to
  invoke `lint_imports_command()` (not the lower-level `lint_imports()` this gotcha note used)
  directly rather than treating the module path as a fallback.
- No `psql` client installed. Neon/Dynatrace/Statuspage credentials were not needed through the
  pure-backend sprints; the live loop (`python -m src.composition.run`, STORY-016) reads four secrets
  from the environment via `composition/settings.py::load_live_secrets()` (`DYNATRACE_ENV_URL`,
  `DYNATRACE_API_TOKEN`, `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY` — see CLAUDE.md "Live-loop
  secrets"). **Correction (sprint-36, STORY-043, 2026-07-02 audit finding M4):** before STORY-043,
  nothing ever loaded a `.env` file — `load_settings`/`load_live_secrets` only ever read
  `os.environ`, so "from the environment / a gitignored `.env`" was FALSE; the documented
  `.env`-based recipe crashed with `MissingLiveSecretError` even with a fully-populated repo-root
  `.env`, unless the secrets were also separately exported into the shell. STORY-043 fixed this by
  calling `dotenv.load_dotenv()` at the two process entrypoints ONLY (`run.py::main`, before
  `load_settings`/`load_live_secrets`; and `composition/asgi.py` module scope, before
  `create_app()`) — never inside `load_settings`/`load_live_secrets` themselves, so DB-gated/unit
  tests calling those directly with explicit env are unaffected (still NOT part of the six-command
  DoD gate; every test uses recorded fixtures or explicit `monkeypatch` env). `load_dotenv()`'s
  default `override=False` semantics mean an already-exported env var always wins over `.env`
  (production/Railway, which sets real env vars and ships no `.env` file, is unaffected).
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
- sprint-36 (compile pass): re-pinned verified_sha 6a33edb -> 8237962 — the only CLAUDE.md diff in range is f66ecb0, the SAME commit that updated this article to match it (pin had been placed at the code commit instead of the wiki commit). No Facts changed.
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
- sprint-25: STORY-015a stood up the frontend zone (Vite/React/TS SPA under `frontend/`) and made the
  three frontend DoD commands (`npm test` / `npm run build` / `npm run lint`) live in
  `.scrum/definition-of-done.md` (replacing the placeholder note), documented in CLAUDE.md + added
  `"frontend"` to the ruff `exclude` in the same commit (`08d91e7`). The six backend commands are
  unchanged and untouched by frontend work. verified_sha → 08d91e7.
- sprint-28: STORY-042 made the API HTTP-servable for local dev — added `uvicorn[standard]` to the dev
  extras and `backend/src/composition/asgi.py` (`app = create_app()`, served by
  `uvicorn src.composition.asgi:app --port 8000`). CLAUDE.md gained a "Run the app locally" recipe
  (throwaway DB → export `DATABASE_URL` → uvicorn on :8000 → 2nd terminal `python -m src.composition.run`
  live loop → `npm run dev`). No DoD command changed (still six backend + three frontend); CORS stays
  deferred to STORY-017 (the Vite proxy makes dev same-origin). verified_sha → 6303247.
- sprint-30: re-verified (STORY-044). No DoD-gate or dependency change; the only `pyproject.toml` edit
  was adding `"src.api.v1.topology"` to the `api-feature-independence` import-linter contract's module
  list (see [[architecture-boundary]]) — unrelated to the six backend / three frontend DoD commands or
  the dependency lists this article describes. Still six backend + three frontend commands, all green.
  verified_sha → 280c1e3.
- sprint-31: re-verified (STORY-048, a TEMPORARY feature — see [[sample-mode]]). No DoD-gate or
  dependency change; the only `pyproject.toml` edit was adding `"src.api.v1.sample_mode"` to the
  `api-feature-independence` import-linter contract's module list (see [[architecture-boundary]]) —
  unrelated to the six backend / three frontend DoD commands or the dependency lists this article
  describes. Still six backend + three frontend commands, all green. verified_sha → 0ea652e.
- sprint-36: STORY-043 (defect fix) corrected the "credentials read from the environment / a
  gitignored `.env`" Fact above — that was FALSE before this story (nothing loaded `.env`; only
  `os.environ` was ever read, so the documented `.env`-only local recipe crashed with
  `MissingLiveSecretError`). Added `python-dotenv` to `[project.dependencies]` (runtime — imported
  by `run.py`/`asgi.py`) and a `load_dotenv()` call at each of the two process entrypoints only
  (never inside `load_settings`/`load_live_secrets`, so the six-command DoD gate and its
  explicit-env tests are unaffected). Still six backend + three frontend commands, all green.
  verified_sha → 6a33edb.
- sprint-38: re-verified (STORY-055 — frontend design-system foundation). The staleness sweep
  flagged this article because `CLAUDE.md` and `frontend/package.json` both changed (the Geist/
  Geist Mono font swap: `@fontsource/inter`/`@fontsource/jetbrains-mono` replaced by
  `@fontsource/geist`/`@fontsource/geist-mono`, and CLAUDE.md's frontend-zone paragraph updated to
  match — see [[frontend-zone]]). Neither change touches this article's Facts: the frontend DoD
  gate is still the same three commands (`npm test`/`npm run build`/`npm run lint`), still
  INDEPENDENT of the six backend commands, and `package.json`'s `dependencies` shape (a `dependencies`
  + `devDependencies` split with the three scripts) is unchanged — only which font packages sit in
  `dependencies`. No DoD-gate or command change. verified_sha → 298f170.
- sprint-41 (STORY-070): re-verified. `run.py::main` gained a vendor-id drift probe call at startup
  (see [[ingest-service-and-pull-loop]]); no dev-setup, DoD command, or `run.py`-as-entrypoint Fact
  this article describes changed. verified_sha → 4d3fd7a.
- sprint-43 (quality-review fix loop, M1): `scripts/dev_db.py`'s `DEV_DB_READY_TIMEOUT_SECONDS`
  parse moved from a bare module-scope `float(...)` (which crashed pytest collection on an
  empty/garbage value, since `conftest.py` imports `dev_db` at collection time) to a lazy
  `_ready_timeout_seconds()` function called from `wait_for_postgres` at call time. The knob name
  and 60s default this article documents are UNCHANGED — no Fact edit needed; re-verified only.
  verified_sha → 10a2d73.
- sprint-44 (STORY-064 wiki-blast-radius sweep, pilot): the mechanical sweep flagged this article
  for the sprint-44 gate-hygiene commit (0889259) that moved DoD command #2 OFF the `lint-imports`
  exe shim — a Windows Application Control policy now blocks it outright (not the old
  corrupted-launcher flake this article's gotcha used to describe) — onto the module-path
  invocation `python -c "from importlinter.cli import lint_imports_command;
  lint_imports_command()"` (same 5 contracts, same check). `CLAUDE.md`/`.scrum/definition-of-done.md`
  both updated in that commit; this article's Fact #2 and the `lint-imports` gotcha note were the
  only stale text (no other DoD command or dependency changed). No STORY-064 backend/frontend code
  change touches this article's `code_refs`. verified_sha → 0da9568.
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged the Fact citing
  `backend/tests/test_spine_schema.py` as the named example of a DB-gated test consuming the
  `migrated_db` fixture — not in `code_refs`, so the sweep could never have caught it drifting.
  Added to `code_refs` (a defining exemplar of the fixture-consumption pattern this article
  documents). No Fact text changed. verified_sha → 678ff0d.
