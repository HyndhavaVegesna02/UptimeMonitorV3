# Sprint 42 Review — API-restructure "now" phase

- **Date:** 2026-07-10
- **Goal:** Land the API-restructure "now" phase (proposal `docs/superpowers/specs/2026-07-10-api-restructure-design.md`): mechanically enforce the api zone's thinness (074) and give cross-feature HTTP policy an owned home — central error registry (075) and one window-policy home (076) — with the error contract and existing endpoint tests frozen.
- **Committed:** 7 pts (STORY-074 2 + STORY-075 3 + STORY-076 2).
- **Accepted:** 7 pts. PO accepted all three at review (2026-07-10), + one MINOR follow-up filed (STORY-077).
- **Execution mode:** External implementation (2026-07-10 working agreement) — PO ran the sprint with an external AI agent on `sprint-42`; orchestrator did planning + post-implementation verification (Opus spec + Opus quality reviewers per story + an independent six-gate DoD re-run).

## Verification (independent, orchestrator @ HEAD 3ea7e31)

Six-gate DoD, re-run from scratch on a fresh throwaway Postgres (not trusting reported evidence):

| Gate | Result |
| --- | --- |
| `pytest` | **540 passed** (valid signal — `--ignore` the two STORY-073 Docker-lifecycle flakes; both pass **8/8 in isolation**; contention proven per the 2026-07-06 agreement: empty diff since `sprint-42-start`, a different lifecycle test fails each contended run). |
| `lint-imports` | **8 kept, 0 broken** (the 3 new contracts + the SyntacticValidationError hoist keep every boundary). |
| `check_fk_direction.py` | 11 FKs, 0 violations. |
| `alembic upgrade head` | exit 0. |
| `ruff check .` | exit 0. |
| `ruff format --check .` | 558 files formatted. |

Scope discipline confirmed at the diff level: **frontend/ diff empty**; **no existing test modified** (only new test files added); the fix loop touched **no** core/adapters/composition logic (one blank-line ruff touch to `app.py` aside).

## Per-story outcome

### STORY-074 — enforcement contracts + zone-layout meta-test → ACCEPTED
- `api-outward-independence` + `adapters-edge-only` added verbatim (proposal §6.3); the api zone's thinness is now a build failure, not a convention (closes the proposal's G1).
- `test_zone_layout.py` verified non-vacuous: derives the feature set from the filesystem, the contract list from parsing `pyproject.toml`, and the mounted routers from the v1 aggregator, asserting set-equality + router inclusion; all three drift directions raise; underscore packages excluded so `_shared` can't false-fail it.
- `architecture-boundary.md` updated 5 → 8 contracts with symbol citations.
- Spec PASS / Quality APPROVE.

### STORY-075 — `_shared` error registry → ACCEPTED (after a fix loop)
- Created `api/v1/_shared/` (errors registry + `install_error_handlers` wired into `create_app`; documented empty `middleware.py` seam for STORY-017); stripped per-feature exception mapping from availability/history controllers + decisions/maintenance services (closes G2/G5).
- **Review found two MAJOR quality findings** (external impl): (MAJOR-1) a global `ValueError → 422` catch-all masking server-side 500s as client errors; (MAJOR-2) the "registry" was 7 copy-pasted handler closures.
- **Fix loop (orchestrator-dispatched Sonnet)** resolved both **entirely within the api zone**: dict-driven registry + handler factory; base `ValueError` handler dropped; a single `SyntacticValidationError` hoisted into `_shared/validation.py` (features re-export it — the legal direction; `api-shared-no-feature-imports` stays green); and the maintenance non-UTC 422 gap closed *syntactically* (avoiding the pydantic-re-wrap trap — a domain exception would not have propagated as itself). New tests lock a bare-`ValueError`→500 and a non-UTC-maintenance→clean-422.
- Frozen contract verified: status + `{"detail": …}` message reproduced exactly for all four pre-strip mapping sites; none invented, none missed.
- Spec PASS / Quality APPROVE (after fix).

### STORY-076 — `_shared/windowing.py` consolidation → ACCEPTED
- `resolve_window` (24h default policy) hoisted into `_shared`; availability + history services consume it; both private copies deleted (closes the contract-forced duplication G3). Availability's window-LABEL logic stayed feature-local. Grep-clean: no `_DEFAULT_WINDOW_HOURS`/duplicated defaulting remains outside `_shared/windowing.py`.
- Spec PASS / Quality APPROVE.

## Non-blocking items → follow-up
Filed as **STORY-077** (chore):
- MINOR-1: `test_zone_layout.py` couples to FastAPI's private `_IncludedRouter`/`original_router` (fail-loud, works on 0.138.0) — replace with a public-API route assertion or pin the FastAPI lower bound + comment.
- MINOR-2: restore the concurrency-nuance comment dropped from `decisions/service.py` during the strip (the `ProposalNotOpenError → 409` covers both the up-front guard and the lost-race resolve).

## Wiki compile pass
Mechanical staleness sweep over all 13 articles at branch HEAD: one stale (`sample-mode.md`, via a cosmetic ruff blank-line touch to `composition/app.py`) — re-verified (no Facts changed), `verified_sha → 3ea7e31`. `architecture-boundary.md` + `api-five-file-convention.md` were updated during the sprint. All current at merge.

## Demo
Not a UI sprint. Evidence is the six-gate output above + the contract additions (`lint-imports` now proves the api zone cannot import adapters/composition/SQL, and `_shared` cannot import features).
