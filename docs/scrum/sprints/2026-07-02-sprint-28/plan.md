# Sprint 28 — Plan

**Dates:** starts 2026-07-02.
**Goal:** make the FastAPI backend HTTP-servable + document the end-to-end local dev stack (STORY-042).
**Branch:** `sprint-28` (tag `sprint-28-start` @ `5172156`). Committed: 3 pts (velocity mean 5.0 — deliberate under-commit).
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers (3 pts → full pipeline).

This is a BACKEND story. Work is under `backend/src/composition/` + `pyproject.toml` + `CLAUDE.md` +
a test under `backend/tests/`. **No frontend source change** (the frontend already targets the
`/api` proxy). The six backend DoD commands must stay green. CORS stays deferred to STORY-017 (the
Vite dev proxy makes the frontend same-origin locally — no CORS needed).

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green step**,
staging only touched files (never `git add -A`), branch verified `sprint-28` before each commit.

## Key facts (verified against code)

- `backend/src/composition/app.py::create_app(*, database_url=None, ..., config_dir=None)` is the
  composition root. On the production path (no repos injected) it: reads settings
  (`load_settings()` — needs `DATABASE_URL` env), builds the SQLAlchemy engine, sets
  `app.state.seed_config = load_config(config_dir or settings.config_dir)` and
  `app.state.db_engine`, wires all repos + `ApprovalService`, and mounts the v1 router at
  `/api/v1`. The `lifespan` seeds topology at boot when `seed_config` + `db_engine` are set.
- So a production ASGI app is simply `create_app()` with `DATABASE_URL` set in the environment and
  a valid `config_dir` (verify `settings.config_dir` defaults to `config/apps`; if it does,
  `create_app()` needs no args — otherwise pass `config_dir="config/apps"` explicitly).
- `uvicorn` is NOT installed and NOT in `pyproject.toml`; there is no module-level `app`. The API
  has only been exercised via FastAPI `TestClient` in pytest (see `backend/tests/test_seed.py`,
  `test_*_endpoint.py`).
- The live pull-loop entrypoint already exists: `python -m src.composition.run`
  (`backend/src/composition/run.py`), reads `.env` secrets (Dynatrace + Statuspage) — it produces
  observations → proposals → publications into the DB. This story does NOT change it; it documents
  running it alongside the API server.

## STORY-042 — Serve the API locally + dev stack (3 pts) — AC1–AC5

- [ ] **T1 — Add the ASGI server dependency (AC1).** Add `uvicorn[standard]` to
      `[project.optional-dependencies] dev` in `pyproject.toml`. Re-install (`pip install -e ".[dev]"`)
      so `.venv/Scripts/uvicorn.exe` exists. Update the CLAUDE.md tooling inventory table (uvicorn —
      local ASGI dev server) in the SAME commit (command-sync agreement). Verify `ruff check`,
      `ruff format --check`, `lint-imports`, `pytest` all still green (a dep add touches no code).
- [ ] **T2 — ASGI entrypoint + servability test (AC2, AC3), TDD.** Write the failing DB-gated test
      FIRST (`backend/tests/test_asgi.py` or extend `test_seed.py`), using the shared `migrated_db`
      fixture: construct the app via the SAME wiring the entrypoint uses — `create_app(
      database_url=<the migrated_db pooled URL>, config_dir="config/apps")` — wrap in a FastAPI
      `TestClient`, and assert `GET /api/v1/components` → 200 returning the seeded components (topology
      seed ran). Also assert the entrypoint module exposes a FastAPI `app`. Then create
      `backend/src/composition/asgi.py`:
      ```python
      """ASGI entrypoint for local/dev serving: `uvicorn src.composition.asgi:app`.
      Reads DATABASE_URL + the topology config from the environment/settings (dossier §17)."""
      from src.composition.app import create_app
      app = create_app()
      ```
      **Import-time caveat:** `app = create_app()` builds a real engine at import, so it needs
      `DATABASE_URL` set. Do NOT let a bare `import src.composition.asgi` run at pytest COLLECTION
      time without a DB (it would raise/So build). Keep the module a trivial wrapper and drive the
      servability assertion through `create_app(...)` directly in the test (with the fixture URL);
      if you also assert on the module's `app`, import it INSIDE the test body after the
      `migrated_db` fixture has set `DATABASE_URL` (e.g. `importlib.import_module`), never at module
      top. Confirm `lint-imports` stays green (composition may import both `src.api` and the app —
      no boundary violation).
- [ ] **T3 — Document the local dev stack (AC4).** Add a "Run the app locally" section to CLAUDE.md
      with the ordered recipe:
      1. `python scripts/dev_db.py up` (throwaway Postgres; prints `DATABASE_URL` + `DATABASE_URL_DIRECT`).
      2. Export `DATABASE_URL` (the plain-libpq pooled form it printed).
      3. Start the API: `.venv/Scripts/python.exe -m uvicorn src.composition.asgi:app --port 8000`
         (serves `/api/v1/*`; the boot seed populates components).
      4. In a SECOND terminal, `python -m src.composition.run` (reads `.env` secrets) to populate
         proposals/observations/publications via the live loop.
      5. `cd frontend && npm run dev` — the Vite proxy now reaches the API; no ECONNREFUSED.
      Correct the existing stale line in the frontend-zone description of CLAUDE.md ("a locally
      running uvicorn instance of the backend") to point at this real recipe. Note that the API
      server and the live loop are two separate processes sharing the same `DATABASE_URL`, and that
      CORS is unneeded locally (same-origin via the proxy; real CORS is STORY-017).
- [ ] **T4 — Gates + blast radius (AC1–AC4 mechanical).** All six backend DoD commands exit 0 on a
      clean committed tree (`pytest`, `lint-imports`, `check_fk_direction.py`, `alembic upgrade head`,
      `ruff check`, `ruff format --check`). Wiki blast radius: `pyproject.toml` + `CLAUDE.md` are in
      several articles' `code_refs` (notably `dev-setup-and-dod.md`) — the orchestrator runs the
      mechanical sweep at the compile pass; flag which articles your diff touches.

**AC5 (manual, PO-observed at review):** the full stack runs end to end (npm run dev with no proxy
errors; Dashboard shows components; after the live loop, Approvals/History/Publications populate).
This needs the PO's live `.env` credentials, so it is exercised at review by the PO OR carved out as
a tracked follow-up — NOT marked done by promise (2026-06-29 live-verification agreement). The
implementer does NOT need creds; AC1–AC4 are the mechanical gate.

## Conventions checklist (held at quality review)
- Module + public-symbol docstrings citing the relevant dossier § (mirror the peer composition
  modules — `run.py`, `app.py`, `settings.py`); the new `asgi.py` gets a module docstring.
- TDD: the servability test is written and fails before `asgi.py` exists; no production code before
  its test.
- Command-sync: the uvicorn dep + the run recipe land in `pyproject.toml`/CLAUDE.md in the same
  commits as the code that needs them.
- Scoped staging; commit-after-green; no `git add -A`.
- No boundary violation: `asgi.py` lives in `composition` (the zone permitted to import both sides);
  `lint-imports` stays at 5 kept / 0 broken.
- Import-time safety: the servability test must not trigger a real-engine build at pytest collection
  without a DB (see T2 caveat).
- No frontend change; no CORS work (STORY-017).

## Guardrails (implementer)
- Build to THIS plan + `docs/scrum/stories/STORY-042-serve-api-locally-dev-stack.md` + dossier §17 —
  never chat history. Do NOT write `.scrum/` board state; do NOT run reviewers or merge — the
  orchestrator owns the back half. You do NOT need live credentials (AC5 is the PO's manual step).
- Genuine ambiguity → STOP and report the exact question. Effort > 3× the 3-pt estimate → STOP.
- Report: steps done + commit SHA each; every gate command + exit + tail; the exact uvicorn command
  that serves the app; wiki articles your diff touches; anything noticed-but-not-done; or the
  blocking question.

## Sequencing rationale
T1 (dep) first so `uvicorn` exists for any manual check. T2 is the core: test-first servability +
the thin entrypoint (the import-time-engine caveat is the one real subtlety — handled by driving the
assertion through `create_app` with the fixture DB). T3 docs capture the two-process recipe the PO
chose. T4 gates. Single story, low code volume; the risk is entirely in the entrypoint wiring +
not breaking test collection, which T2 addresses head-on.
