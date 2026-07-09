# Sprint 42 Plan — API-restructure "now" phase

- **Goal:** Land the API-restructure "now" phase from the accepted 2026-07-10 proposal
  (`docs/superpowers/specs/2026-07-10-api-restructure-design.md`): mechanically enforce the api
  zone's thinness (STORY-074), give cross-feature HTTP policy an owned home — one error registry
  (STORY-075), one window-policy home (STORY-076) — with the error contract and all existing
  endpoint tests frozen.
- **Stories:** STORY-074 (2pt) → STORY-075 (3pt) → STORY-076 (2pt) = 7 pts. Strictly sequential.
- **Branch:** `sprint-42` (cut from main @ `dc95d46`, tag `sprint-42-start`).
- **Execution mode:** EXTERNAL implementation (2026-07-10 working agreement). The implementing
  agent works ONLY on `sprint-42`, never merges to main, never edits `.scrum/sprint-current.yaml`
  (board state is the orchestrator's ledger — 2026-06-25 agreement). It MAY tick the checkboxes in
  THIS file and append to story-file History sections.
- **Verification (after implementation):** orchestrator runs Opus spec + Opus quality reviewers
  per story + an independent full six-gate DoD re-run before any board=done.

## Non-negotiables (read first)

1. **This plan + the three story files + the proposal §6 are the whole contract.** Build to them,
   never to chat history. The proposal document is in-repo and binding for the contract TOML
   (§6.3) and target layout (§6.2).
2. **All three stories are backend-only.** `frontend/` must have an EMPTY diff at sprint end.
3. **Frozen error contract (075/076):** every EXISTING test under `backend/tests/` passes
   UNMODIFIED. If you believe a test must change, STOP and record a blocker in the story file
   History instead — do not edit the test.
4. **TDD with a commit after every green step.** Never more than ~30 minutes of work uncommitted.
   Stage only the files you touched — never `git add -A` (2026-06-24 agreement).
5. **The six backend DoD gates** (run from repo root, venv binaries):
   `pytest` · `lint-imports` · `python scripts/check_fk_direction.py` · `alembic upgrade head` ·
   `ruff check .` · `ruff format --check .` — all exit 0 on a CLEAN COMMITTED tree (uncommitted
   changes invalidate a gate run — 2026-06-29 agreement). DB-gated commands need the throwaway DB:
   `.venv/Scripts/python.exe scripts/dev_db.py up` prints both URLs (pooled plain-libpq form →
   `DATABASE_URL`; direct `+psycopg` form → `DATABASE_URL_DIRECT`). One `pytest` invocation at a
   time against one DB (2026-07-02 agreement). Known flake: `test_dev_db_cli.py` /
   `test_dev_db_fixture.py` may false-red under Docker contention (filed STORY-073); if ONLY those
   fail, prove contention (empty diff + green in isolation) and record the resource-isolated
   signal per the 2026-07-06 agreement.
6. **Wiki blast radius is the MECHANICAL sweep** (2026-06-28): for EVERY article in
   `docs/scrum/wiki/*.md`, run `git diff <its verified_sha>..HEAD -- <its code_refs>`; any output →
   the article must be updated (or explicitly re-verified) with `verified_sha` bumped to the
   story's final commit. Commit ARTICLE-BY-ARTICLE (2026-07-03). Wiki Facts cite SYMBOLS
   (`file.py::name`), never bare line numbers (2026-06-27).

## Conventions checklist (2026-06-27 agreement — quality review holds ALL new code to this)

- (a) Module + public class/function docstrings citing the relevant dossier § / proposal §,
  mirroring peer modules' style (`api/v1/availability/service.py`, `core/services/pipeline.py`).
- (b) Frozen value/result types with cross-field invariants enforce them via
  `model_validator(mode="after")` + tests for both rejected and valid shapes. (No new value types
  are expected this sprint; rule stands if one appears.)
- (c) Empty-input AND non-aligned-boundary tests where applicable (windowing: both-None case is
  REQUIRED by STORY-076 AC).
- (d) Scoped staging — never `git add -A`.
- (e) Follow existing import/naming/structure patterns; no new style.
- (f) Any new `api/v1/<feature>/` would need the five-file-shape test (2026-06-28) — note:
  `_shared` is deliberately NOT a feature (no router, no five-file shape, underscore-prefixed) and
  must NOT be added to the `api-feature-independence` contract list.
- (g) API endpoints reject tz-naive datetimes with 422 at the edge (2026-06-28) — unchanged
  behavior; do not weaken existing validators while stripping error mapping.

---

## STORY-074 — Enforcement contracts + zone-layout meta-test (2pt)

AC: see `docs/scrum/stories/STORY-074-api-enforcement-contracts.md` (binding).

- [ ] **Step 1 (test first):** write `backend/tests/test_zone_layout.py`:
  - derives the feature set from the filesystem: package dirs under `backend/src/api/v1/` whose
    name does not start with `_` (today: decisions, health, components, approvals, maintenance,
    availability, history, publications, topology, sample_mode);
  - parses `pyproject.toml` for the `api-feature-independence` contract's `modules` list; asserts
    set equality with `src.api.v1.<dir>` derived from the filesystem;
  - asserts each feature's router is reachable in the aggregated v1 router
    (`backend/src/api/v1/__init__.py`) — e.g. by importing the aggregator and checking each
    feature's routes are mounted (route path prefixes or router objects; pick the least brittle
    assertion that still fails when an `include_router` line is missing);
  - edge behavior: an underscore-prefixed package (future `_shared`) is EXCLUDED by the filesystem
    derivation — assert the exclusion logic explicitly (e.g. a unit-level check of the discovery
    helper against a tmp dir, or a comment-pinned filter test), so STORY-075 cannot false-fail it.
  - Run: test passes against today's tree (it is an invariant test, not red/green TDD — its
    "red" is demonstrated by the mutation check in Step 2).
- [ ] **Step 2 (prove the guard):** temporarily (in-memory / not committed) verify the test FAILS
  when a feature is removed from the parsed contract list — e.g. parametrize the assertion helper
  and unit-test it with a doctored list. The committed form must prove the failure mode without a
  committed broken state.
- [ ] **Step 3:** add the two contracts to `pyproject.toml`, verbatim from proposal §6.3:
  `api-outward-independence` (forbidden: `src.api` → `src.adapters`, `src.composition`,
  `sqlalchemy`, `psycopg`, `httpx`) and `adapters-edge-only` (forbidden: `src.adapters` →
  `src.api`, `src.composition`). Run `lint-imports`: expect **7 kept, 0 broken**. Commit.
- [ ] **Step 4:** full six-gate run on the clean tree; then the mechanical wiki sweep. Expected
  stale: `architecture-boundary.md` (its `code_refs` include `pyproject.toml`; its Facts state the
  contract inventory — update the count 5→7 and add the two new contracts as Facts with symbol
  citations). Update/re-verify every article the sweep reports, commit article-by-article.
- [ ] **Step 5:** append the story-file History entry (what was done, final SHA), tick these boxes.

## STORY-075 — `_shared` foundation: central error registry (3pt)

AC: see `docs/scrum/stories/STORY-075-api-shared-error-registry.md` (binding).

- [ ] **Step 0 (inventory, committed as a note in the story file History):** read ALL 10 feature
  packages; enumerate every `(domain exception → status, message shape)` mapping that exists today
  and WHERE it lives (known: `availability/controller.py` maps SyntacticValidationError→422 and
  SignalNotFoundError→404 and SignalIntervalUnconfiguredError→409, duplicated across its two
  endpoints; `history/controller.py` maps its validation error→422; `decisions/service.py` and
  `maintenance/service.py` map in the service layer). The registry covers EXACTLY this inventory —
  nothing invented (2026-06-29 "do not invent" precedent).
- [ ] **Step 1 (tests first):** new `backend/tests/test_shared_errors.py`: builds a minimal app
  via `create_app` with fakes (mirror `test_availability_endpoint.py`'s pattern), drives each
  registered exception through a real endpoint, asserts status + `{"detail": <today's exact
  message>}`. Also asserts an UNREGISTERED exception still propagates (500 via TestClient
  `raise_server_exceptions` behavior unchanged) — the registry must not become a catch-all.
- [ ] **Step 2:** implement `backend/src/api/v1/_shared/__init__.py` + `errors.py`
  (registry dict + `install_error_handlers(app)`; docstrings cite proposal §3.4 G2/§6.2) and the
  documented empty `middleware.py` seam (docstring names STORY-017; no logic). Wire
  `install_error_handlers(app)` into `composition/app.py::create_app`. Commit on green.
- [ ] **Step 3 (strip, one feature per commit):** remove the local mapping from
  `availability/controller.py`, `history/controller.py`, `decisions/service.py`,
  `maintenance/service.py` — the feature code lets domain exceptions propagate. After EACH
  feature's strip: its endpoint tests pass UNMODIFIED; commit. Edge rule: if any stripped site
  turns out to add per-feature information to the message (not just `str(exc)`), STOP — record a
  blocker in the story History rather than changing the wire message.
- [ ] **Step 4:** add the `api-shared-no-feature-imports` contract (proposal §6.3 verbatim);
  `lint-imports` → **8 kept, 0 broken**. Confirm `_shared` is NOT in `api-feature-independence`
  and `test_zone_layout.py` (from 074) stays green. Commit.
- [ ] **Step 5:** grep-proof: no `HTTPException` construction remains under
  `backend/src/api/v1/` feature packages (health's plain 200 and any FastAPI-internal uses are
  fine; record the grep output in the story History). Full six-gate run on the clean tree.
- [ ] **Step 6:** mechanical wiki sweep. Expected stale: `api-five-file-convention.md` (revise to
  "five files + `_shared`", admission criteria = cross-feature HTTP policy only, per proposal
  §6.4) and possibly `architecture-boundary.md` (pyproject touch). Commit article-by-article;
  History entry; tick boxes.

## STORY-076 — `_shared/windowing.py` consolidation (2pt)

AC: see `docs/scrum/stories/STORY-076-api-shared-windowing.md` (binding).

- [ ] **Step 1 (tests first):** `backend/tests/test_shared_windowing.py` for
  `resolve_window(since, until, now) -> (since, until)`:
  - both None → exactly `(now − 24h, now)`;
  - only `until` given → `(until − 24h, until)`;
  - only `since` given → `(since, now)`;
  - both given → passthrough unchanged;
  - inputs are tz-aware datetimes (validators upstream guarantee this — do NOT re-validate here;
    document that contract in the docstring).
- [ ] **Step 2:** implement `backend/src/api/v1/_shared/windowing.py` with the constant
  (`DEFAULT_WINDOW_HOURS = 24`) + `resolve_window`, semantics IDENTICAL to today's
  `availability/service.py::_resolve_window` defaulting (read it first; the window LABEL logic
  stays in availability — only defaulting moves). Docstring cites proposal §3.4 G3. Commit on
  green.
- [ ] **Step 3:** consume it from `availability/service.py` (delete `_resolve_window`'s
  defaulting + the private constant; keep label computation feature-local) and from
  `history/service.py` (delete the inlined defaulting + its `_DEFAULT_WINDOW_HOURS`). After EACH:
  that feature's endpoint tests pass UNMODIFIED; commit per feature.
- [ ] **Step 4:** grep-proof: `_DEFAULT_WINDOW_HOURS`/duplicated defaulting exists nowhere under
  `api/v1/` except `_shared/windowing.py` (record in story History). Full six-gate run
  (lint-imports still 8/0). Mechanical wiki sweep (expect `api-five-file-convention.md` and/or
  availability-related articles if their `code_refs` cover the touched services). History entry;
  tick boxes.

## Sprint-end (external agent's last act)

- [ ] All three stories' boxes ticked, tree clean, all commits pushed to `origin/sprint-42`.
- [ ] A final summary appended to each story file's History: final SHA, gate results
  (command + exit code + output tail), the wiki articles updated, and any deviations/blockers.
- [ ] Do NOT merge to main. Do NOT close the sprint. Report back to the PO — the orchestrator
  session then runs Opus spec + quality reviews and the independent gate re-run.
