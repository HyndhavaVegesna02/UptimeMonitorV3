# Sprint 43 Plan — harden the gate + name the read side

- **Goal:** Make the flaky dev_db lifecycle gate deterministic (STORY-073), clear the sprint-42
  review minors (STORY-077), and land the core/queries CQRS-lite move (STORY-078 — proposal §8,
  PO-triggered).
- **Stories & order:** STORY-073 (3pt) → STORY-078 (3pt) → STORY-077 (2pt) = 8 pts. Sequential.
  073 first so the DoD gate is trustworthy for the rest; 078 next (biggest blast radius); 077 last.
- **Branch:** `sprint-43` (cut from main @ `ca340ed`, tag `sprint-43-start`).
- **Execution mode:** EXTERNAL implementation. Work ONLY on `sprint-43`; NEVER merge to main; NEVER
  edit `.scrum/sprint-current.yaml` or `.scrum/backlog.yaml` (orchestrator's ledger). You MAY tick
  the checkboxes in THIS file and append to story-file History sections.
- **Verification (after implementation):** orchestrator runs Opus spec + Opus quality reviewers per
  story + an independent full six-gate DoD re-run before any board=done.

## Non-negotiables (read first)
1. **This plan + the three story files + (for 078) proposal §8 are the whole contract.** Build to
   them, not to chat history. Proposal: `docs/superpowers/specs/2026-07-10-api-restructure-design.md`.
2. **All three stories are backend-only.** `frontend/` must have an EMPTY diff at sprint end.
3. **TDD; commit after every green step** (~30 min max uncommitted). Stage only files you touch —
   never `git add -A` (2026-06-24 agreement).
4. **The six backend DoD gates** (repo root, venv binaries): `pytest` · `lint-imports` ·
   `python scripts/check_fk_direction.py` · `alembic upgrade head` · `ruff check .` ·
   `ruff format --check .` — all exit 0 on a CLEAN COMMITTED tree (2026-06-29). DB gates need the
   throwaway DB: `.venv/Scripts/python.exe scripts/dev_db.py up` (exports `DATABASE_URL`=plain-libpq,
   `DATABASE_URL_DIRECT`=+psycopg). One `pytest` at a time against one DB (2026-07-02).
   **After STORY-073 lands, `pytest` must be run WITHOUT `--ignore` (no lifecycle-flake carve-out) —
   the whole point of 073 is that the canonical single command is deterministic.** Before 073 lands
   (i.e. while verifying 073 itself), the prior valid-signal carve-out may be referenced only to
   prove the before/after.
5. **Wiki blast radius = the MECHANICAL sweep** (2026-06-28): for EVERY article in
   `docs/scrum/wiki/*.md`, `git diff <its verified_sha>..HEAD -- <its code_refs>`; any output → update
   or re-verify (bump `verified_sha`). Commit ARTICLE-BY-ARTICLE (2026-07-03). Facts cite SYMBOLS
   (`file.py::name`), not bare line numbers (2026-06-27).

## Conventions checklist (quality review holds ALL new code to this — 2026-06-27)
- (a) Module + public class/function docstrings citing the relevant dossier §/proposal §, mirroring
  peers (`core/services/pipeline.py`, `core/services/availability.py`).
- (b) New frozen value/result types enforce cross-field invariants via `model_validator(mode="after")`
  + tests (078 MOVES `AvailabilityResult` — keep its existing validator + tests intact, just relocated).
- (c) Empty-input AND non-aligned-boundary tests where applicable.
- (d) Scoped staging — never `git add -A`.
- (e) Follow existing import/naming/structure patterns; no new style.
- (f) Command-sync (2026-06-23): if 073 adds/changes a `scripts/dev_db.py` knob or any DoD/build/run
  command, update CLAUDE.md in the SAME commit.
- (g) Resource-lifecycle teardown-on-failure (2026-06-25): 073 must preserve teardown on every
  failure path (including partial-setup failure) with the regression tests still proving no leak.

---

## STORY-073 — deterministic dev_db lifecycle gate (3pt)
AC & decided mechanism: `docs/scrum/stories/STORY-073-dev-db-lifecycle-tests-flaky.md` (binding).
Mechanism = robust, tunable container readiness in `scripts/dev_db.py::wait_for_postgres` (keep the
lifecycle tests IN the canonical gate; do NOT marker-gate them out; container-reuse rejected).

- [x] **Step 1 (characterize):** reproduce the flake (full-suite run on a warm host), capture the
  exact failure (readiness timeout at `wait_for_postgres` vs container-start/alembic-subprocess
  failure). Record the root cause in the story History.
- [x] **Step 2 (robust readiness):** in `scripts/dev_db.py`, make readiness survive a loaded Docker
  host — a patient retry/backoff loop with a tunable overall budget (module constant + env override,
  e.g. `DEV_DB_READY_TIMEOUT_SECONDS`; sensible default raised from today's). A genuinely-failed
  container still raises cleanly AND tears down (teardown-on-failure preserved — 2026-06-25). If a
  behavior/knob/command changes, update CLAUDE.md same commit (2026-06-23).
- [x] **Step 3 (prove determinism):** run the canonical `pytest` (single invocation, NO `--ignore`,
  warm host) ≥3 times INCLUDING `test_dev_db_cli.py` + `test_dev_db_fixture.py`; all green. Record
  the runs as evidence. If robust readiness alone is insufficient, apply the sanctioned fallback:
  SERIALIZE the container-spawning lifecycle tests relative to each other (file lock / ordering) —
  still in the gate, not removed.
- [x] **Step 4:** confirm the lifecycle assertions are UNCHANGED (teardown-on-failure, idempotent
  up, no leaked container). Full six-gate on the clean tree. Mechanical wiki sweep (expect
  `dev-setup-and-dod` — `scripts/dev_db.py` is in its `code_refs`). Commit article-by-article.
- [x] **Step 5:** story History entry (root cause, final SHA, the ≥3 green full-suite runs); tick boxes.

## STORY-078 — core/queries CQRS-lite move (3pt)
AC: `docs/scrum/stories/STORY-078-core-queries-cqrs-lite.md` (binding). Proposal §8. **Scope = the
MOVE + the layering contract ONLY.** Do NOT add the read/write feature contracts or touch
`api/dependencies.py`'s ApprovalService wiring (deferred/rejected — proposal §8, §5.3).

- [x] **Step 1 (create + move):** create `backend/src/core/queries/__init__.py` +
  `core/queries/availability.py`; move `AvailabilityCalculator`, `AvailabilityResult`,
  `rollup_group`, `bucket_into_cycles` (and their private helpers) WHOLE from
  `core/services/availability.py` (delete from there). Keep the `collapse` import from
  `core/services/pipeline.py` (queries→services pure fn is allowed). Preserve `AvailabilityResult`s
  `model_validator` + docstrings verbatim (relocated, not rewritten). Module docstring cites proposal §8.
- [x] **Step 2 (update import sites):** repoint every importer to `core.queries.availability`:
  `composition/orchestrate.py` (`bucket_into_cycles`), `api/v1/availability/service.py`
  (`AvailabilityCalculator`), and all test imports (`backend/tests/test_availability.py` et al.).
  Grep-proof: NO reference to `core.services.availability` remains anywhere (record the grep).
  Test import-path updates are a mechanical move — allowed; do NOT change any assertion/behavior.
- [x] **Step 3 (layering contract):** change `pyproject.toml` `core-internal-layering` to
  `layers = ["src.core.queries", "src.core.services", "src.core.ports", "src.core.domain"]`.
  `lint-imports` → **8 kept, 0 broken**. Verify nothing in `core/services/` imports `core.queries`
  (services-below-queries; the P4 "pipeline never consults availability" is now a build failure) and
  `core-independence` still holds (core.queries inherits vendor-freedom).
- [x] **Step 4:** full six-gate on the clean tree (canonical `pytest`, no `--ignore` — 073 already
  landed). Behavior frozen: every test passes (import paths updated only). Mechanical wiki sweep —
  expect `core-pipeline-and-availability`, `canonical-types-and-ports`, `architecture-boundary` (add
  the `queries` layer fact + the 4th-subpackage tree) and any article whose `code_refs` list
  `core/services/availability.py` (update the path). Commit article-by-article.
- [x] **Step 5:** story History entry (files moved, final SHA, grep-proof, gate results); tick boxes.

## STORY-077 — sprint-42 review minors (2pt)
AC: `docs/scrum/stories/STORY-077-sprint42-review-minors.md` (binding).

- [ ] **Step 1 (MINOR-1, test first):** rewrite `backend/tests/test_zone_layout.py`'s router-inclusion
  check to use a PUBLIC FastAPI API (inspect `app.routes` / mounted path prefixes) instead of the
  private `fastapi.routing._IncludedRouter` / `.original_router`. It MUST still fail on all three
  drift directions: (i) a feature dir missing from the `api-feature-independence` contract list;
  (ii) a feature dir whose router is not mounted by the v1 aggregator; (iii) an extra unregistered
  feature dir. Prove each failure mode (parametrized helper / doctored inputs), not just the happy
  path. If no clean public equivalent exists, INSTEAD pin the FastAPI lower bound in `pyproject.toml`
  + add a comment flagging the private-API dependency (and say why in the story History).
- [ ] **Step 2 (MINOR-2):** restore the concurrency-nuance comment to
  `backend/src/api/v1/decisions/service.py` (or `core/services/approval.py`) — that
  `ProposalNotOpenError → 409` covers BOTH the up-front open-state guard AND a lost-race resolve
  (concurrent double-submit surfaced by the repo; 2026-06-28 TOCTOU agreement). `_shared/errors.py`
  is now a bare mapping and carries no such context.
- [ ] **Step 3:** full six-gate on the clean tree; mechanical wiki sweep; commit article-by-article;
  story History entry; tick boxes.

## Sprint-end (external agent's last act)
- [ ] All boxes ticked, tree clean, everything pushed to `origin/sprint-43`.
- [ ] Each story file History updated: final SHA, six-gate results (command + exit code + tail), wiki
  articles updated, deviations/blockers. For 073: paste the ≥3 green full-suite (no-`--ignore`) runs.
- [ ] Do NOT merge to main. Do NOT close the sprint. Report back to the PO for orchestrator review.
