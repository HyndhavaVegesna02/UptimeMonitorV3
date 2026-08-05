---
title: Dev setup and the Definition-of-Done gate
code_refs: [pyproject.toml, CLAUDE.md, .scrum/definition-of-done.md, backend/tests/conftest.py, .gitattributes, frontend/package.json, backend/src/composition/asgi.py, backend/src/composition/run.py]
verified_sha: 0769b0a
verified_sprint: sprint-69
status: verified
# Re-stamped 2026-08-02 (sprint-67, STORY-210 quality-review fix round; commit 0084326). CLAUDE.md
# and .scrum/definition-of-done.md both changed again, but neither change touches a Fact in this
# article: CLAUDE.md gained one clarifying sentence distinguishing `ruff.exe` (preventive
# module-form move, NOT blocked) from the three shims that ARE blocked -- the commands and their
# invocations are unchanged from the STORY-210 re-verification below. .scrum/definition-of-done.md
# only corrected a retro citation's wording (the sprint-66 retro named the next casualties as
# "ruff.exe or the npm toolchain", not "ruff.exe" alone) -- no command text changed. Bare re-stamp:
# no DoD command, env precondition or contract changed.
# Re-verified 2026-08-02 (sprint-67, STORY-210). Backend commands 3 and 4 in the "backend DoD
# gate" Fact below changed FOR REAL this time: `ruff check .` / `ruff format --check .` ->
# `python -m ruff check .` / `python -m ruff format --check .` (PO-approved, preventive --
# ruff.exe was NOT blocked, `ruff --version` -> `ruff 0.15.20` exit 0 at sprint-67 planning; same
# reasoning as commands 1/2/5's earlier moves off their shims). `.scrum/definition-of-done.md`
# and CLAUDE.md changed in the same commit. The `[tool.ruff] exclude` bullet's command names were
# also updated to match. The article's "sprint-22: STORY-016c" History line (re-derived at this
# commit: `:222-223`) is a dated history note about what was literally true then and was
# deliberately LEFT UNCHANGED -- rewriting it would falsify the record. Frontend commands
# (`npm test`/`npm run build`/`npm run lint`)
# UNCHANGED: no `-m` module form exists for `npm`; `node <npm_root>/bin/npm-cli.js --version` is
# a measured shim-free analogue (11.6.2, exit 0) but its behaviour under the policy is UNVERIFIED
# and adopting it is a separate PO decision, out of scope here (STORY-210 AC7).
# Re-verified 2026-08-01 (OUT OF SPRINT — PO-directed process work on branch
# process/ratchet-brake-from-sprint-66, not a story). CLAUDE.md was pruned 420 -> 292 lines.
# All five Facts in this article that cite CLAUDE.md were re-read against the pruned file:
#   - "Key commands" (venv + editable install)            -> unchanged, still there
#   - "Key commands" (host port 8001, not 8000)           -> unchanged, still there
#   - "Key commands" (lint_imports_command module form)   -> unchanged, still there
#   - "Live-loop secrets" (the four env secrets)          -> unchanged, section heading intact
#   - "commands + frontend/ layout in CLAUDE.md"          -> PARTIALLY MOVED, noted inline below
# The frontend COMMAND table is still in CLAUDE.md; the frontend directory TREE moved to
# frontend/README.md + wiki/frontend-zone.md. The Fact is a historical statement about commit
# 08d91e7 and stays true as history, but a reader following it would not find the layout, so an
# inline pointer was added rather than leaving the citation silently misleading.
# NOT a bare re-stamp: no DoD command, env precondition or contract changed.
# Re-verified 2026-07-30 (sprint-64) by the orchestrator. Changed code_ref in range: CLAUDE.md
# (STORY-182's demo-loop section + STORY-181-era credential prose). Not a bare re-stamp: the
# sprint measured a real DoD-gate property that belongs here and was missing -- a green pytest
# with Docker down silently skips the whole persistence floor and still exits 0. Added as a Fact
# with its reproduction recipe and the operational rule adopted this sprint.
# Re-verified 2026-07-30 (sprint-65) WITHOUT content change. Its code_refs were touched only
# incidentally: run.py gained a rejected_repo argument (STORY-190), conftest.py and the DoD were
# untouched by this sprint's stories beyond STORY-188's encoding repair. Every Fact re-read and
# still accurate; the DoD command list and env preconditions are unchanged.
# Re-stamped 2026-07-30 (sprint-65 quality-review round): CLAUDE.md's 'Two things to know'
# bullet was rewritten (it still claimed DOWN/DEGRADED cannot reach the pipeline). No Fact in
# THIS article was affected -- its commands and env preconditions are unchanged.
---

## Facts (verified against code)
- Python 3.13; setuptools build backend (`pyproject.toml:1-3`). Runtime deps: fastapi,
  pydantic>=2, pyyaml, httpx, python-dotenv,
  boto3 (`pyproject.toml` â€” `[project] dependencies`; pyyaml added sprint-16 STORY-040a for the config
  loader, httpx promoted to a runtime dep sprint-20 STORY-016 for the Grail + Statuspage HTTP
  executors, python-dotenv added sprint-36 STORY-043 so the two process entrypoints can load a
  `.env` file, boto3 added sprint-46 STORY-082 for the AWS/DynamoDB persistence migration).
  Dev extras: pytest, import-linter, ruff, uvicorn[standard] (`pyproject.toml` â€”
  `[project.optional-dependencies] dev`; `uvicorn` added sprint-28 STORY-042 as the local ASGI dev
  server â€” see "Run the app locally" below).
- Setup: `python -m venv .venv` then `.venv/Scripts/python.exe -m pip install -e ".[dev]"`
  (Windows; call `.venv` binaries directly). Documented in `CLAUDE.md` "Key commands".
- pytest is configured with `testpaths = ["backend/tests"]` (`pyproject.toml:27-28`).
- **The backend DoD gate is FIVE bare commands**, each must exit 0
  (`.scrum/definition-of-done.md`; enumerate them with
  `python .claude/skills/yourteam/scripts/yt_gate.py --list`, which is the count of record):
  1. `python -m pytest`
     (2026-07-31, sprint-66/STORY-197: invocation moved OFF the `pytest` exe shim for the
     SAME reason as command 2 below — the machine's Windows Device Guard / Application
     Control policy began blocking `.venv/Scripts/pytest.exe` MID-SPRINT, green at 11:16
     UTC and blocked at 16:33 UTC the same day with no code change in between. Same tests,
     same rootdir, same `testpaths`; module-path invocation instead. PO-approved; the
     underlying policy problem is STORY-210.)
  2. `python -c "from importlinter.cli import lint_imports_command; lint_imports_command()"`
     (2026-07-12, sprint-44: invocation moved OFF the `lint-imports` exe shim â€” a Windows
     Application Control policy now blocks it on this machine; same check, module-path
     invocation instead. It enforces **NINE** contracts (STORY-206, sprint-69, added the
     ninth): core-independence, core-internal-layering, adapters-independence,
     api-feature-independence, api-outward-independence, adapters-edge-only,
     api-shared-no-feature-imports, src-no-tests, inbound-adapters-dont-persist — the
     count read off the runner's own `Contracts: 9 kept, 0 broken.` line, which is the
     only reliable source for it)
  3. `python -m ruff check .`
     (2026-08-02, sprint-67/STORY-210: invocation moved OFF the `ruff` exe shim to its module
     form — PREVENTIVE, not a repair: `ruff.exe` was still permitted at sprint-67 planning
     (`ruff --version` -> `ruff 0.15.20`, exit 0), but the same Device Guard / Application
     Control policy had already widened twice mid-sprint without warning (commands 1, 2 and 5 in
     this list), so the retro named `ruff.exe` as the likeliest next casualty. Same check, same
     rules, same files; `python -m ruff --version` returns the identical version.)
  4. `python -m ruff format --check .`
     (2026-08-02, sprint-67/STORY-210: same reasoning as command 3.)
  5. `python -c "from cfnlint.runner import main; main()" infra/stack.yaml`
     (2026-07-31, sprint-66/STORY-197: same Device Guard cause as commands 1 and 2, but
     cfn-lint needed a DIFFERENT answer — the package has no `__main__`, so `python -m
     cfnlint` does NOT work; this is its real console-script entry point,
     `cfn-lint = cfnlint.runner:main`. A separately blocked `regex` DLL was a second
     symptom, cleared by reinstalling regex 2026.7.10 -> 2026.7.19.)
     (added STORY-088, sprint-49, in the same DoD amendment that
     RETIRED `alembic upgrade head` and `python scripts/check_fk_direction.py` — that is why the
     backend count went 6 → 5 and why "six backend commands" appears throughout this article's
     History; it was true then, and stopped being true at sprint-49)
  Command 2 became real during Sprint 0 (bootstrap); 3 and 4 were added in Sprint 11.
  - `[tool.ruff]` carries `exclude = [".agents", ".venv", "frontend"]` (`pyproject.toml`; `.agents`
    STORY-016c, `frontend` STORY-015a): `.agents/` is untracked third-party skills tooling that otherwise
    makes `python -m ruff check .` / `python -m ruff format --check .` exit non-zero; `frontend/` is
    the JS/TS SPA (no Python) excluded so the Python formatter/linter stays scoped to backend code.
    `.venv` is already gitignored and conventionally skipped â€” listed for defensiveness.
- **The frontend has its own three-command DoD gate (live as of STORY-015a, sprint-25), run from
  `frontend/`** (`.scrum/definition-of-done.md` "Commands (frontend)"; commands in `frontend/package.json`):
  1. `npm test` â€” Vitest run-once (`"test": "vitest run"`)
  2. `npm run build` â€” `tsc -b && vite build` (the type-check is part of the build gate)
  3. `npm run lint` â€” ESLint flat config (`eslint .`)
  These are INDEPENDENT of the five backend commands: the frontend is isolated (no backend import, no
  shared build step), so a backend-only story never runs the npm gates and a frontend-only story never
  runs the backend five. **Eight commands in total.** The `.scrum/definition-of-done.md` frontend section stopped being a
  "placeholder until then" note and became live in the same commit (`08d91e7`) that documented the
  commands + `frontend/` layout in CLAUDE.md (command-sync agreement; the command table is still
  in CLAUDE.md, but the directory tree moved to the frontend README and the frontend-zone wiki
  article in the 2026-08-01 prune). Toolchain: Vite + React +
  TypeScript (strict), Vitest + React Testing Library + MSW (the only mocked I/O edge in frontend tests),
  npm on Node 24. Playwright/E2E is deferred to a later integration story.
- **Running the app locally (STORY-042; `.env` loading STORY-043):** the FastAPI API is served via
  the ASGI entrypoint `backend/src/composition/asgi.py` (`app = create_app()` â€” reads the topology config,
  default `config/apps`, so the boot-time seed runs), launched with
  `uvicorn src.composition.asgi:app --port 8000`. The Vite dev proxy (`/api` â†’ `:8000`) then reaches it.
  Full local stack (CLAUDE.md "Run the app locally"): start DynamoDB Local container â†’ export `DYNAMO_ENDPOINT_URL` (or place
  it in a repo-root `.env` â€” see the STORY-043 correction above) â†’ create tables via `python scripts/create_tables.py`
  â†’ the uvicorn command â†’ a 2nd terminal running the live loop `python -m src.composition.run`
  (populates proposals/observations/publications) â†’ `npm run dev`. Two processes share one DynamoDB Local;
  no CORS anywhere: locally the Vite proxy makes it same-origin, and in production CloudFront
  does (STORY-089), so no CORS work is queued. `api/v1/_shared/middleware.py` is an empty
  seam whose docstring (corrected STORY-181, sprint-63) now states this directly — no CORS
  required, dev via the Vite proxy, prod same-origin behind CloudFront — and no longer names the
  archived STORY-017. Before STORY-042 the API had only ever run in-process via `TestClient` (no
  ASGI server, no module-level app).
- **Standard way to obtain a throwaway DynamoDB Local (STORY-082):**
  Docker container running `amazon/dynamodb-local`. Start command:
  `docker run -d --name uptime_dynamo -p 8001:8000 amazon/dynamodb-local -jar DynamoDBLocal.jar -inMemory`
  Tables are created by `python scripts/create_tables.py`. **Host port 8001, not 8000** — the API
  owns 8000 in the local-stack recipe, and this line said `8000:8000` until sprint-62, which
  collides with it (corrected against `CLAUDE.md` "Key commands", the recipe actually run).
- Under `pytest`, the session-scoped `dynamo_local` fixture (`backend/tests/conftest.py`, via
  `dynamo_local.resolve_dynamo()`): reuses `DYNAMO_ENDPOINT_URL` if already set externally; else spawns a
  throwaway `amazon/dynamodb-local` on a free port if Docker is available (PID+UUID-unique container name,
  to avoid collisions between concurrent runs), tearing it down in a finalizer; else skips DynamoDB-gated tests.
  A function-scoped `clean_dynamo_tables` fixture deletes and recreates tables before each test to ensure
  complete, order-independent test isolation on a shared Local instance.
- **A GREEN `pytest` DOES NOT BY ITSELF MEAN THE PERSISTENCE FLOOR RAN — and the gate cannot tell you.**
  That last "else" above is silent: with Docker down and `DYNAMO_ENDPOINT_URL` unset, every
  DynamoDB-gated test SKIPS and `pytest` still **exits 0**, so `yt_gate.py` records a PASS.
  Measured at sprint-64's branch point (`805287f`), same commit, same command, minutes apart:
  * Docker down, no `DYNAMO_ENDPOINT_URL` → **`561 passed, 53 skipped`**, exit 0, gate PASS
  * Docker up + `DYNAMO_ENDPOINT_URL=http://127.0.0.1:8021` → **`614 passed, 0 skipped`**, exit 0
  53 tests — the entire persistence floor — vanished without a single red signal. The exit code is
  identical in both cases, which is why this is a Fact and not a footnote: the DoD's own mechanical
  floor has a hole exactly the shape of "Docker wasn't running".
  **Operational rule adopted for sprint 64 and recommended as standing practice:** record the
  pass/skip COUNTS on every backend gate record, and treat a nonzero skip count as an INCOMPLETE
  gate, not a pass. See `.scrum/sprint-current.yaml`'s per-story `dod_gate.env_note` entries for the
  worked form.
  (Sprint 64, discovered by the orchestrator while establishing the sprint baseline. Pinned by no
  test — this is a property of the fixture's skip path plus `pytest`'s exit-code contract, so per
  working agreement A2 it is labelled here as an observation with its reproduction recipe, not as a
  test-pinned behavioural Fact.)
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
- No `psql` client installed and no SQL database in use (Neon Postgres + Alembic were retired
  by STORY-087, sprint-49). Dynatrace/Statuspage credentials were not needed through the
  pure-backend sprints; the live loop (`python -m src.composition.run`, STORY-016) reads four secrets
  from the environment via `composition/settings.py::load_live_secrets()` (`DYNATRACE_ENV_URL`,
  `DYNATRACE_API_TOKEN`, `STATUSPAGE_PAGE_ID`, `STATUSPAGE_API_KEY` â€” see CLAUDE.md "Live-loop
  secrets"). **Correction (sprint-36, STORY-043, 2026-07-02 audit finding M4):** before STORY-043,
  nothing ever loaded a `.env` file â€” `load_settings`/`load_live_secrets` only ever read
  `os.environ`, so "from the environment / a gitignored `.env`" was FALSE; the documented
  `.env`-based recipe crashed with `MissingLiveSecretError` even with a fully-populated repo-root
  `.env`, unless the secrets were also separately exported into the shell. STORY-043 fixed this by
  calling `dotenv.load_dotenv()` at the two process entrypoints ONLY (`run.py::main`, before
  `load_settings`/`load_live_secrets`; and `composition/asgi.py` module scope, before
  `create_app()`) â€” never inside `load_settings`/`load_live_secrets` themselves, so DB-gated/unit
  tests calling those directly with explicit env are unaffected (still NOT part of the six-command
  DoD gate; every test uses recorded fixtures or explicit `monkeypatch` env). `load_dotenv()`'s
  default `override=False` semantics mean an already-exported env var always wins over `.env`
  (production/AWS ECS Fargate, which sets real env vars and ships no `.env` file, is unaffected —
  `run.py`'s comment corrected STORY-181, sprint-63; it had said "Railway").
- **Line endings are normalized to LF in the repo** via `.gitattributes` (`* text=auto eol=lf`
  + `binary` rules for `*.png/jpg/jpeg/gif/ico/pdf/woff/woff2`; STORY-018). Gotcha: the index
  blobs were already LF, so `git add --renormalize .` stages nothing â€” the CRLF a Windows
  checkout shows in the *working tree* comes from the contributor's global `core.autocrlf=true`
  (a checkout-time conversion), not from repo content. `.gitattributes` keeps it that way and
  stops the per-commit `LF will be replaced by CRLF` warnings.

## Inference (synthesis, not verified)
- `.scrum/definition-of-done.md` is the single canonical DoD (Sprint 0 retro working
  agreement, 2026-06-23). The root `definition-of-done.md` is now just a one-line pointer to
  it â€” no second editable copy.

## History
- sprint-36 (compile pass): re-pinned verified_sha 6a33edb -> 8237962 â€” the only CLAUDE.md diff in range is f66ecb0, the SAME commit that updated this article to match it (pin had been placed at the code commit instead of the wiki commit). No Facts changed.
- sprint-0: created (compile pass folding STORY-001/002/003 setup learnings).
- sprint-3: updated (STORY-019 shared throwaway-DB harness) â€” added the
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
  unchanged and untouched by frontend work. verified_sha â†’ 08d91e7.
- sprint-28: STORY-042 made the API HTTP-servable for local dev â€” added `uvicorn[standard]` to the dev
  extras and `backend/src/composition/asgi.py` (`app = create_app()`, served by
  `uvicorn src.composition.asgi:app --port 8000`). CLAUDE.md gained a "Run the app locally" recipe
  (throwaway DB â†’ export `DATABASE_URL` â†’ uvicorn on :8000 â†’ 2nd terminal `python -m src.composition.run`
  live loop â†’ `npm run dev`). No DoD command changed (still six backend + three frontend); CORS stays
  deferred to STORY-017 (the Vite proxy makes dev same-origin). verified_sha â†’ 6303247.
- sprint-30: re-verified (STORY-044). No DoD-gate or dependency change; the only `pyproject.toml` edit
  was adding `"src.api.v1.topology"` to the `api-feature-independence` import-linter contract's module
  list (see [[architecture-boundary]]) â€” unrelated to the six backend / three frontend DoD commands or
  the dependency lists this article describes. Still six backend + three frontend commands, all green.
  verified_sha â†’ 280c1e3.
- sprint-31: re-verified (STORY-048, a TEMPORARY feature â€” see [[sample-mode]]). No DoD-gate or
  dependency change; the only `pyproject.toml` edit was adding `"src.api.v1.sample_mode"` to the
  `api-feature-independence` import-linter contract's module list (see [[architecture-boundary]]) â€”
  unrelated to the six backend / three frontend DoD commands or the dependency lists this article
  describes. Still six backend + three frontend commands, all green. verified_sha â†’ 0ea652e.
- sprint-36: STORY-043 (defect fix) corrected the "credentials read from the environment / a
  gitignored `.env`" Fact above â€” that was FALSE before this story (nothing loaded `.env`; only
  `os.environ` was ever read, so the documented `.env`-only local recipe crashed with
  `MissingLiveSecretError`). Added `python-dotenv` to `[project.dependencies]` (runtime â€” imported
  by `run.py`/`asgi.py`) and a `load_dotenv()` call at each of the two process entrypoints only
  (never inside `load_settings`/`load_live_secrets`, so the six-command DoD gate and its
  explicit-env tests are unaffected). Still six backend + three frontend commands, all green.
  verified_sha â†’ 6a33edb.
- sprint-38: re-verified (STORY-055 â€” frontend design-system foundation). The staleness sweep
  flagged this article because `CLAUDE.md` and `frontend/package.json` both changed (the Geist/
  Geist Mono font swap: `@fontsource/inter`/`@fontsource/jetbrains-mono` replaced by
  `@fontsource/geist`/`@fontsource/geist-mono`, and CLAUDE.md's frontend-zone paragraph updated to
  match â€” see [[frontend-zone]]). Neither change touches this article's Facts: the frontend DoD
  gate is still the same three commands (`npm test`/`npm run build`/`npm run lint`), still
  INDEPENDENT of the six backend commands, and `package.json`'s `dependencies` shape (a `dependencies`
  + `devDependencies` split with the three scripts) is unchanged â€” only which font packages sit in
  `dependencies`. No DoD-gate or command change. verified_sha â†’ 298f170.
- sprint-41 (STORY-070): re-verified. `run.py::main` gained a vendor-id drift probe call at startup
  (see [[ingest-service-and-pull-loop]]); no dev-setup, DoD command, or `run.py`-as-entrypoint Fact
  this article describes changed. verified_sha â†’ 4d3fd7a.
- sprint-43 (quality-review fix loop, M1): `scripts/dev_db.py`'s `DEV_DB_READY_TIMEOUT_SECONDS`
  parse moved from a bare module-scope `float(...)` (which crashed pytest collection on an
  empty/garbage value, since `conftest.py` imports `dev_db` at collection time) to a lazy
  `_ready_timeout_seconds()` function called from `wait_for_postgres` at call time. The knob name
  and 60s default this article documents are UNCHANGED â€” no Fact edit needed; re-verified only.
  verified_sha â†’ 10a2d73.
- sprint-44 (STORY-064 wiki-blast-radius sweep, pilot): the mechanical sweep flagged this article
  for the sprint-44 gate-hygiene commit (0889259) that moved DoD command #2 OFF the `lint-imports`
  exe shim â€” a Windows Application Control policy now blocks it outright (not the old
  corrupted-launcher flake this article's gotcha used to describe) â€” onto the module-path
  invocation `python -c "from importlinter.cli import lint_imports_command;
  lint_imports_command()"` (same 5 contracts, same check). `CLAUDE.md`/`.scrum/definition-of-done.md`
  both updated in that commit; this article's Fact #2 and the `lint-imports` gotcha note were the
  only stale text (no other DoD command or dependency changed). No STORY-064 backend/frontend code
  change touches this article's `code_refs`. verified_sha â†’ 0da9568.
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged the Fact citing
  `backend/tests/test_spine_schema.py` as the named example of a DB-gated test consuming the
  `migrated_db` fixture â€” not in `code_refs`, so the sweep could never have caught it drifting.
  Added to `code_refs` (a defining exemplar of the fixture-consumption pattern this article
  documents). No Fact text changed. verified_sha â†’ 678ff0d.
- sprint-46 (STORY-082): Added boto3 dependency and set up the session-scoped dynamo_local
  fixture and clean_dynamo_tables for DynamoDB Local container lifecycle integration. verified_sha -> abd8609.
- sprint-47 (STORY-080): Hardened container connection readiness verification to retry and recover from transient connection drops under load, and collision-proofed the CLI tests (`test_dev_db_cli.py`) by dynamically allocating unique container names and ports. verified_sha -> 50a7bd9.
- sprint-50 (STORY-089): CLAUDE.md gained the append-only deployed-topology section (live stack facts, no dev-setup or DoD content touched). Facts unchanged; re-verified. verified_sha -> 235fc37.
- sprint-62 (STORY-148): the mechanical sweep flagged `backend/tests/conftest.py` in this
  article's `code_refs`. The only change there is a second `sys.path` insertion (repo-root
  `tools/`, alongside the existing `scripts/` one) so the new `tools/demo_engine/` package
  (STORY-148's Grail-shaped demo HTTP server) is importable from `backend/tests/demo_engine/`.
  The `dynamo_local`/`clean_dynamo_tables` fixture behaviour this article's Facts describe is
  byte-identical; re-verified, no Fact text changed. verified_sha -> ba00bd5.
- 2026-07-29 (sprint-62 close, PO-directed docs pass): **three stale COUNTS corrected in the
  Facts, all of which had been wrong for sprints while the code stood still.** (1) "The DoD gate
  is four bare commands" listed four and omitted `cfn-lint infra/stack.yaml` — added STORY-088 in
  sprint-49, in the same amendment that retired `alembic upgrade head` and
  `check_fk_direction.py`. It is FIVE. (2) "same 5 import-linter contracts" — the runner prints
  `Contracts: 8 kept`; contracts 5-7 (api-outward-independence, adapters-edge-only,
  api-shared-no-feature-imports) landed without this article, `CLAUDE.md`, or the DoD file being
  updated. (3) "the six backend commands" (twice) — a pre-sprint-49 count that this article
  contradicted three lines above its own "four". The History entries below keep "six" where they
  describe sprints in which six was correct; only the Facts are corrected. The article now points
  at `yt_gate.py --list` as the count of record, so the next reader does not have to trust a
  number typed by hand. Same failure mode as STORY-149's anti-flap Fact: a claim can rot while
  its code is untouched, which is exactly what the git-arithmetic sweep cannot see.
  `CLAUDE.md` (a `code_ref`) was rewritten in the same pass; re-verified against it.
  verified_sha -> 19c9c1a.
- sprint-63 (STORY-176, story + fix round; STORY-180): the sweep flagged `CLAUDE.md` and
  `backend/tests/conftest.py`. `CLAUDE.md` grew a "Two things to know before you touch anything"
  section and a Part-2a scenario-player paragraph (both about the demo engine, not dev setup or the
  DoD gate — see [[demo-engine]]); `conftest.py` gained a reasoning COMMENT above the pre-existing
  `tools/` `sys.path` front-insertion (STORY-180 AC6/minor 8) with no behavioural change. Neither
  touches a Fact this article states: still five backend + three frontend DoD commands, still eight
  import-linter contracts, same `dynamo_local`/`clean_dynamo_tables` fixture mechanics. No Fact text
  changed; re-verified only. verified_sha -> c07831b.
- sprint-63 (STORY-181): the sweep flagged `asgi.py`, `run.py`, `pyproject.toml`. Two Facts above
  directly quoted comments this story retired: `middleware.py`'s docstring no longer names the
  archived STORY-017 (it now states plainly that no CORS is required), and `run.py`'s
  `load_dotenv()` comment no longer says "Railway" (production is AWS ECS Fargate, STORY-089).
  `asgi.py`'s reworded `DATABASE_URL` note and the `pyproject.toml` vendor-subpackage comment are
  unrelated to any DoD command, contract count, or fixture mechanics this article states. Both
  Facts above corrected; verified_sha -> b272c32.
- sprint-63 (STORY-181, AC7 pass): the sweep re-flagged `CLAUDE.md` after its own "History —
  superseded" bullets were corrected to say STORY-181 fixed the Railway/Vercel and STORY-017
  comments (rather than claiming they "still" name them). No Fact in THIS article quotes that
  History section's wording. Re-verified only; no further Fact change. verified_sha -> c6d7657.
- sprint-68 (STORY-204 fix round): the sweep flagged `run.py`. STORY-204's fix round expanded the
  vendor-id drift probe's call-site comment (correcting a stale "never raises" claim — see
  [[ingest-service-and-pull-loop]]/[[zone-rules]]); this article cites no line number or quoted
  wording from that comment, and states no Fact about DoD commands, contract counts, or fixture
  mechanics that it touches. Re-verified only; no Fact changed. verified_sha -> bfa5f77.
- sprint-68 (STORY-204 second fix round): the sweep flagged `run.py` again. This round reordered
  (did not change the substance of) the same comment's opening sentence so its fail-fast scope is
  stated on its own line (see [[dynatrace-adapter]]/[[zone-rules]]); this article still cites no
  line number or quoted wording from it. Re-verified only; no Fact changed. verified_sha ->
  d554227.
- sprint-69 (STORY-206, verified_sha bumped `d554227` -> `0769b0a`): `pyproject.toml` gained a
  ninth `lint-imports` contract, `inbound-adapters-dont-persist` (ZR-1's guard — see
  [[zone-rules]]). The Facts bullet naming all contracts by number and by name is corrected from
  EIGHT to NINE, with the ninth contract added to the list and the quoted runner output moved from
  `Contracts: 8 kept` to `Contracts: 9 kept`. The DoD command count is UNCHANGED at eight — the new
  contract runs inside the existing import-boundary command; "Eight commands in total" and the
  History entries' own dated counts are untouched by design.
