# Sprint 20 — Review

**Story:** STORY-016 — First end-to-end thread (live demo). **5 pts. Accepted.**
**Branch:** `sprint-20` (`sprint-20-start..` HEAD). **Final SHA:** `d9c2a77` (code) + `0648cff` (wiki).

## What shipped
The monitoring loop is now WIRED LIVE end to end (gate-green via recorded fixtures; the live SaaS
observation is the manual post-merge smoke by design):

- **Real Dynatrace Grail DQL executor** (`adapters/inbound/dynatrace/grail_executor.py`) — `httpx` POST
  to `…/platform/storage/query/v1/query:execute`, `Api-Token` auth, maps `records` → the normalizer
  row shape; `GrailQueryError` on non-2xx; empty records → `[]`.
- **Real Statuspage HTTP executor** (`adapters/outbound/statuspage/http_executor.py`) — real PATCH,
  parsed JSON, `StatuspageApiError` on non-2xx (so `BestEffortPublisher` swallows on the recovery path).
- **Settings + config mapping** — `load_live_secrets()`/`LiveSecrets` (four env vars, named error on
  missing; API boot path unchanged); `ComponentConfig.statuspage_component_id` + `Config.statuspage_mapping()`.
- **Orchestration threaded through `run_periodic`** + the live driver `composition/run.py`
  (`build_live_loop` + `python -m src.composition.run`) assembling
  `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))` → `DecideService`, one loop per signal,
  engine disposed on every exit path.
- `httpx` promoted to a runtime dependency; CLAUDE.md gains the run command + the four live-loop secrets.

## DoD gate (orchestrator-run, committed tree `d9c2a77`)
All six exit 0: **pytest 419 passed** · lint-imports 5/0 · check_fk_direction 11/0 · alembic up-to-date
(no new migration) · ruff check · ruff format (153 files).

## Review — one fix loop
Both Opus reviewers (spec + quality) **independently found the same blocking pair**:

1. **CRITICAL — live loop could not start.** `run.py` built the publisher chain with
   `RecordingPublisher(publisher=…)` / `BestEffortPublisher(publisher=…)`, but both constructors take
   `delegate=`. `build_live_loop` raised `TypeError` on the first call — `python -m src.composition.run`
   would die on startup. Reproduced concretely by the orchestrator.
2. **CRITICAL — the test that should have caught it lied.** `test_run_live_loop.py` patched every
   constructor `__init__` to a no-op and asserted only `assert_called_once()`, so the wrong kwargs sailed
   through and the nesting was never checked — the exact "green test over a broken path" pattern the
   2026-06-29 spec-rigor agreement was written to catch. **The agreement worked**: the gate was green,
   but the reviewers (not the gate) caught it.
3. **MAJOR** — stray `httpx2` in the dev extra (broke `pip install -e ".[dev]"`).
4. **MINOR** — CLAUDE.md missing the four live-secret env vars (folded into the fix).

**Fix (PO-authorized inline, `d9c2a77`):** `publisher=` → `delegate=`; the assembly test rewritten to
construct the REAL objects (only `run_periodic` patched) and assert the
`BestEffort→Recording→Statuspage` `isinstance` chain + the six orchestration extras on each
`run_periodic` call — so it now errors under the old wiring and genuinely guards the regression; `httpx2`
dropped; the four secrets documented.

## AC outcome
- AC1 (Dynatrace executor) — **MET**. AC2 (Statuspage executor) — **MET**. AC3 (settings + mapping) —
  **MET**. AC4 (live driver + orchestration threading) — **MET after fix**. AC5 (live SaaS observation)
  — **manual post-merge smoke** (runbook in plan.md T5); not gate-verified by design.

## Wiki blast radius
Compile pass `0648cff`: 8 articles updated/re-verified (config-layer, dynatrace-adapter,
statuspage-publish, ingest-service-and-pull-loop, dev-setup-and-dod, migrations-and-db,
architecture-boundary, api-five-file-convention). Mechanical sweep: **0 stale / 0 missing refs / 0 bad
links** across all 11.

## Verdict
**STORY-016 accepted — 5/5.** The backend is not just complete but now wired for live operation. Only
the credentialed live smoke + deployment (STORY-017) and the frontend (STORY-015) remain.
