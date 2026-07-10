# Sprint 43 Review — harden the gate + name the read side

- **Date:** 2026-07-11
- **Goal:** Make the flaky dev_db lifecycle gate deterministic (073), clear the sprint-42 review minors (077), and land the core/queries CQRS-lite move (078 — proposal §8, PO-triggered) so the availability read-model is a fenced 4th core subpackage and "the pipeline never consults availability" becomes a build failure.
- **Committed:** 8 pts (073:3 + 078:3 + 077:2). **Accepted:** 8 pts — PO accepted all three (2026-07-11).
- **Execution mode:** External implementation (2026-07-10 agreement, continued). External agent implemented on `sprint-43`; orchestrator did planning + post-implementation verification (Opus spec + Opus quality per story + independent six-gate re-run).

## Verification (independent, orchestrator @ HEAD ecf614a → 6859f17)

Six-gate DoD, re-run from scratch on a fresh throwaway Postgres:

| Gate | Result |
| --- | --- |
| `pytest` | **557 passed × 2, canonical command with NO `--ignore`** — including `test_dev_db_cli.py` + `test_dev_db_fixture.py`. STORY-073's goal met: the single canonical command is deterministic; the sprint-41/42 `--ignore` carve-out is retired. |
| `lint-imports` | **8 kept, 0 broken** — `core-internal-layering = [queries, services, ports, domain]`; nothing in `core/services` imports `core.queries`. |
| `check_fk_direction.py` | 11 FKs, 0 violations. |
| `alembic upgrade head` | exit 0. |
| `ruff check .` / `ruff format --check .` | clean / 560 files. |

Frontend diff empty; STORY-078 move confirmed pure (validator + computation byte-identical).

## Per-story outcome

### STORY-073 — deterministic dev_db lifecycle gate → ACCEPTED (after a fix loop)
- `scripts/dev_db.py::wait_for_postgres` rebuilt as a patient retry/backoff loop with a tunable budget (`DEV_DB_READY_TIMEOUT_SECONDS`, default 30→60s); teardown-on-failure preserved on every path (readiness timeout AND alembic RuntimeError both route through `stop_container`). Lifecycle tests unweakened. CLAUDE.md synced.
- **Review found MAJOR M1** (external impl): the new `DEV_DB_READY_TIMEOUT_SECONDS = float(os.environ.get(...))` ran at MODULE scope, so a bad/empty value crashed pytest *collection* (confirmed by orchestrator repro) — a robustness regression in the very harness the story hardens.
- **Fix loop** (orchestrator Sonnet): guarded lazy `_ready_timeout_seconds()` (missing/empty/non-numeric → 60s), resolved at call time; **+ m5** new hermetic `test_dev_db_readiness.py` (8 tests) covering the parse + retry/timeout — the coverage whose absence let M1 slip.
- Spec PASS / Quality APPROVE (after fix). Retires the flaky-gate tax that hit sprints 41 & 42.

### STORY-078 — core/queries CQRS-lite move → ACCEPTED (after a fix loop)
- `AvailabilityCalculator` + `AvailabilityResult` + `rollup_group` + `bucket_into_cycles` moved WHOLE from `core/services/availability.py` to `core/queries/availability.py` (deleted from services); `core-internal-layering` gains the `queries` layer above `services` — P4 ("the pipeline never consults availability") is now a build failure. Move verified behavior-frozen. Scope held to the move + contract only (read/write feature contracts + `api/dependencies.py` change stayed deferred per proposal §8).
- **Review found MAJOR M2** (external impl): 5 source/test files kept prose pointers to the deleted `core/services/availability.py`, contradicting the story's own "grep-proof" claim (the grep only caught the dotted-import form).
- **Fix loop:** all 5 repointed to `core/queries/availability.py` (grep clean but the intentional provenance line); **+ m3** restored the module docstring truncated during the move (recovered from the pre-move original + relocation note).
- Spec PASS / Quality APPROVE (after fix).

### STORY-077 — sprint-42 review minors → ACCEPTED
- `test_zone_layout.py` dropped the private FastAPI `_IncludedRouter`/`original_router` for the public `app.openapi()`, non-vacuous on all three drift directions; the decisions TOCTOU concurrency comment restored (decisions/service.py + approval.py).
- **m4** (near-tautological meta-test) folded into the fix loop: the router-inclusion check extracted into a shared helper both the real test and the meta-test call.
- Spec PASS / Quality APPROVE.

## Wiki compile pass
Mechanical sweep at branch HEAD: 2 stale (`config-layer.md`, `sample-mode.md`) — both only via STORY-078's `pyproject.toml` layering-contract line, irrelevant to their subjects → re-verified (no Facts changed), `verified_sha → 6859f17`. During the fix loop the agent also updated 6 articles for STORY-078 (incl. line-anchor fixes) and caught a **pre-existing `migrations-and-db.md` drift** un-bumped since sprint 30. All current at merge.

## Demo
Not a UI sprint. Evidence: the six-gate output above — most saliently, the canonical `pytest` is now deterministic without `--ignore` (073), and `lint-imports` proves the read-model is fenced (078).
