# Sprint 29 — Review

**Goal:** close the approve→publish→write-back dead end (STORY-045).
**Branch:** `sprint-29` (cut from main @ `162783d`). Story commits: `53d3b42` (T1), `a80c622` (T2),
`da156ff` (T3), `7cabee7` (T4), `6d1799a` (T5 wiki). Presented for verdict: 2026-07-03.

## STORY-045 — approved proposals now go somewhere (5 pts, defect)

### What was built
- **`ComponentRepository.set_status`** (new port method) + **`ComponentNotFoundError`**
  (`core/domain/component.py`, mirroring `ProposalNotFoundError`). Postgres adapter: conditional
  `UPDATE` in `engine.begin()`, `rowcount == 0` → the named error. The in-memory fake behaves
  identically — one shared contract test body runs against BOTH implementations.
- **`StatusWritebackPublisher`** (composition decorator): writes `components.status` FIRST (durable,
  propagates on failure), THEN delegates to the publish chain. Sits OUTSIDE `BestEffortPublisher`,
  so only the external Statuspage call is swallowed.
- **`build_publisher`** — the ONE shared chain assembly, now consumed by BOTH composition roots:
  `run.py::build_live_loop` (refactored off its inline block) and `app.py::create_app` (which had NO
  publisher at all — the approve endpoint runs in the API process). Creds+mapping present →
  `StatusWriteback(BestEffort(Recording(Statuspage)))`; absent → `StatusWriteback(Logging)` — so the
  local no-creds dev stack's Dashboard changes too.
- **`ApprovalService`** gains a REQUIRED `publisher` kwarg (deliberately not optional — a silently
  unwired publisher was this very defect). `approve()` publishes `StatusChange(component_id,
  to_status)` AFTER resolution + approval event (commit-first); `reject()` publishes nothing.
- **`load_statuspage_secrets` / `StatuspageSecrets`** (settings): the Statuspage-only optional
  subset, same env-var names, `load_live_secrets` delegates — lets `create_app` wire the chain
  without requiring the Dynatrace vars.
- 16 net-new tests (444 total). No schema change, no API-surface change, no frontend change;
  `decide.py`/`orchestrate.py` untouched (plan D5).

### AC checklist (spec reviewer: PASS, all six MET — tests run, not just read)
- **AC1 approve publishes** — `test_approval.py::test_approval_service_approve_publishes_status_change`
  (spy proves publish AFTER resolution) + `test_decisions.py::test_decision_endpoint_approve_publishes_and_writes_back_status`
  (HTTP approve through the REAL chain → publications row + publisher received the change);
  reject/404/409 paths publish nothing. ✅
- **AC2 status write-back at both triggers** — approve: same HTTP test asserts
  `GET /api/v1/components` returns `degraded`; recovery:
  `test_orchestrate.py::test_recovery_publish_writes_back_component_status`; next-cycle `decide`
  reads it (AC5 e2e cycle 2). ✅
- **AC3 port + parity** — `test_component_repository_contract.py::_assert_set_status_contract` run
  against BOTH impls; the Postgres half actually RAN (Docker-provisioned), not skipped. ✅
- **AC4 commit-first ordering** — as pinned in plan.md (D1/D2), not improvised: DB writes durable
  before the best-effort external call; write-back survives a swallowed Statuspage failure
  (`test_status_writeback_publisher_survives_best_effort_delegate_failure`); publications record
  on success only (unchanged semantics). ✅
- **AC5 recovery reachability** — `test_orchestrate.py::test_degrade_approve_recover_end_to_end`:
  real `orchestrate_signal` + real `ApprovalService` + ONE shared chain: degrade → PROPOSED (nothing
  published) → approve (publish + publication row + status DEGRADED) → next UP cycle fires the
  previously-unreachable `PUBLISHED_RECOVERY` → status back to OPERATIONAL. ✅
- **AC6 gates + wiki** — six-command gate green at `6d1799a` (pytest **444 passed** single run;
  lint-imports 5/0; FK 11/0; alembic 0; ruff both clean). Wiki: 7 articles updated/re-verified
  (5 by the implementer, 2 caught by the orchestrator's mechanical sweep — `run.py`/`settings.py`
  blast radius); final sweep 0 stale / 0 broken across 12. ✅

### Review pipeline (5 pts → full)
- **Spec (Opus): PASS** — all six ACs MET; contract-change rewrites confirmed (no test deleted to a
  gap); assembly tests assert REAL wiring (no `__init__` patching); no scope additions.
- **Quality (Opus): APPROVE** — 0 Critical, 0 Major. Minors (non-blocking, recorded):
  1. `create_app` injected-fakes path: injecting `component_repo` but omitting `publication_repo`
     (or vice versa) silently yields a bare `LoggingPublisher` with no write-back — test-only
     surface; the production path always builds both repos and always gets the full chain.
  2. Pre-existing `publish_best_effort` free function coexists with `BestEffortPublisher` (both
     live; predates this story).
- **Implementer note:** the Sonnet implementer stalled AFTER committing T1–T4 and finishing the T5
  wiki edits (uncommitted). Per the 2026-06-25 crash-recovery agreement the orchestrator inspected
  the tree, kept the coherent completed wiki edits, and committed them (`6d1799a`); the commit
  cadence lost nothing. Retro input.

### Demo (run it yourself, no live creds needed)
1. `.venv/Scripts/python.exe scripts/dev_db.py up` → export the two URLs it prints.
2. `.venv/Scripts/python.exe -m uvicorn src.composition.asgi:app --port 8000`
3. `GET /api/v1/components` → seeded `operational`. Open a proposal (run the live loop against a
   degraded monitor, or insert a proposal row), then
   `POST /api/v1/decisions/{id} {"action":"approve","actor":"you"}` →
   `GET /api/v1/components` now shows the degraded status; `GET /api/v1/publications` has the row
   (with Statuspage creds in the env the change also reaches the real page; without them the
   publish is logged, the write-back still lands).
4. Or just the fast proof: `.venv/Scripts/python.exe -m pytest backend/tests/test_orchestrate.py -q`
   (includes the degrade→approve→recover e2e).

### Verdict
- [x] PO verdict (2026-07-03): **ACCEPT + follow-up chore** — merged to main; the two quality
      minors filed as STORY-047 (`docs/scrum/stories/STORY-047-publisher-wiring-minors.md`, 1 pt,
      ready). Velocity: 5 committed / 5 accepted.
