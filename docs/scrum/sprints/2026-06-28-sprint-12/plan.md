# Sprint 12 — Plan

**Goal:** Open Zone 6 — establish the five-file API convention (dossier §13) and the 4th
import-linter contract (no horizontal feature imports) via the decision/approve exemplar
vertical slice, after rehabilitating the 7 reformat-stale wiki articles so the architecture
article is verified for the API work to update.

**Branch:** `sprint-12` · **Start tag:** `sprint-12-start` · **Baseline:** `2656416` (refinement
on branch; from main `a493a29`).

**Committed: 7 pts** — STORY-034 (2) → STORY-014 (5), in that order.

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)

The **PO implements this plan externally** (Antigravity / Gemini), committing onto `sprint-12`.
The orchestrator does NOT dispatch implementer subagents. **This `plan.md` is the only contract
the implementer builds to** — it is self-contained (file paths, signatures, edge behavior,
conventions, DoD). When implementation is ready, the PO says **"do your review"**; the
orchestrator then diffs `sprint-12-start..HEAD`, runs the full six-command DoD gate, runs the
Opus spec + quality reviewers (STORY-014 only — it is 3+ pts), resolves the wiki forward-blast
radius, and runs review → verdict → merge → retro.

**Commit cadence is the crash-recovery mechanism:** commit after every green TDD step. **Scoped
staging only** — never `git add -A` (working-agreements.md 2026-06-24); stage only the files the
step changed.

### The six-command DoD gate (every story; the non-LLM floor)
1. `pytest` → exit 0
2. `lint-imports` → exit 0 (**4 contracts kept / 0 broken after STORY-014**; 3/0 before it)
3. `python scripts/check_fk_direction.py` → exit 0 (needs a DB)
4. `alembic upgrade head` → exit 0 (needs a DB, DIRECT URL)
5. `ruff check .` → exit 0
6. `ruff format --check .` → exit 0

DB-gated commands (3, 4, and any DB-gated pytest) use the shared helper:
`.venv/Scripts/python.exe scripts/dev_db.py up` (start + migrate + print both URLs) →
run the gate → `scripts/dev_db.py down`. See CLAUDE.md "Throwaway Postgres".

---

## STORY-034 — Rehabilitate the 7 reformat-stale wiki articles (2 pts, gate only) — DO FIRST

**Why first:** it flips `architecture-boundary.md` from `stale` → `verified`, so STORY-014's
forward-blast-radius (Phase F) updates a *verified* article rather than a quarantined one. Also a
low-risk doc-only warm-up. **No `src/` is touched in this story.**

**The 7 stale articles** (frontmatter `status: stale`): `architecture-boundary.md`,
`canonical-types-and-ports.md`, `dynatrace-adapter.md`, `ingest-service-and-pull-loop.md`,
`migrations-and-db.md`, `persistence-adapters.md`, `statuspage-publish.md`
(all under `docs/scrum/wiki/`).

**Citation-syntax authority = working-agreements.md (2026-06-27 amendment), NOT the existing
"verified" articles.** ⚠️ `core-pipeline-and-availability.md` and `dev-setup-and-dod.md` are
`verified` but were re-pinned *before* the retro adopted symbol citations, so they still show
**bare line numbers** (e.g. `` `pipeline.py:40` ``). Do **not** copy their current style. Use:
- `` `file.py::ClassName` `` — for a class
- `` `file.py::function` `` — for a module-level function
- `` `file.py::Class.method` `` — for a method
- `` `file.py` ("section heading") `` — where no symbol applies
- a bare `file.py:NN` is allowed **only** where no symbol fits (a specific constant block / config
  key) and must be flagged for re-pin on any touch.

### Steps (per article — mechanical, doc-only)
- [ ] **034.1** For each of the 7 articles, for **every** Fact that cites `file:line`, re-express
      the citation in the symbol form above. **Verify each Fact against the current code** at
      rehab time (open the file, confirm the symbol exists and the Fact is still TRUE). Commit per
      article (7 small commits) or in a couple of logical batches — each commit green.
- [ ] **034.2** Check the existing **every-Fact-covered** agreement (working-agreements.md
      2026-06-25): every file a Fact addresses must be in that article's `code_refs`. If a Fact
      cites a file not in `code_refs`, either add it to `code_refs` or move the Fact. Do not
      broaden a `code_ref` to a whole directory (working-agreements.md 2026-06-25).
- [ ] **034.3** Lint internal `[[links]]`: every `[[name]]` must resolve to an existing article
      slug (or an archive tombstone). Repoint or prune broken ones.
- [ ] **034.4** In each rehabbed article's frontmatter: flip `status: stale` → `status: verified`
      and bump `verified_sha` to the current `sprint-12` HEAD at rehab time. (The orchestrator
      re-stamps `verified_sha` to the merge commit on main at review — edge-cases.md #4 — so
      "current HEAD" is correct here.) Set `verified_sprint: sprint-12`. **No article is left
      stale.**
- [ ] **034.5** Run the gate (doc-only, but required): `pytest`, `lint-imports`, `ruff check`,
      `ruff format --check` all exit 0. (FK/alembic unaffected by docs but are part of the
      recorded gate — the orchestrator runs the full six at review.)

**AC mapping:** AC1 ← 034.1; AC2 ← 034.4; AC3 ← 034.2 + 034.3; AC4 ← 034.5.

---

## STORY-014 — Five-file API convention + 4th linter contract + decision exemplar (5 pts)

Pipeline: **gate + Opus spec reviewer + Opus quality reviewer** (3+ pts). Spans **three zones**
(core, composition, api). The vertical slice is the **decision (approve/reject)** feature.

### Pre-flight — dependencies
- [ ] **014.0** Confirm `fastapi` + `starlette` `TestClient` (which needs `httpx`) are in
      `pyproject.toml` (`dependencies` for fastapi; `[project.optional-dependencies].dev` for
      httpx if only test-needed). If missing, add them and `pip install -e ".[dev]"`. A dependency
      add is NOT a frozen-tooling change. (If this changes install/run commands, command-sync
      applies — but adding a library to existing extras usually does not.)

### Phase A — port gap: load a proposal by id (TDD)
Today `ProposalRepository` (`core/ports/proposal_repository.py`) exposes only
`get_open(component_id)`; approve/reject need lookup by the endpoint's `proposal_id`.
- [ ] **014.A1** Failing test (`backend/tests/test_proposal_repository_fake.py` or the existing
      fake test module): `FakeProposalRepository.get(proposal_id)` returns the stored proposal,
      and **returns `None`** when absent.
- [ ] **014.A2** Add abstract `get(self, proposal_id: int) -> StatusProposal | None` to the
      `ProposalRepository` port (docstring: "Return the proposal with this id, or None if none
      exists.") + implement on the fake. Green. Commit.
- [ ] **014.A3** Failing **DB-gated** test (use the `migrated_db` fixture, see
      `backend/tests/conftest.py`): `PostgresProposalRepository.get` returns `None` for an unknown
      id and the row for a known id. **Fake/adapter parity** (working-agreements.md 2026-06-26):
      both return `None` on not-found.
- [ ] **014.A4** Implement `PostgresProposalRepository.get` (`adapters/persistence/
      proposal_repository.py`). Green. Commit.

### Phase B — core ApprovalService (TDD, pure, port-backed)
New file `backend/src/core/services/approval.py`. Imports only `src.core.*` (core-independence
stays KEPT). Define domain errors in core (e.g. in `core/domain/` or the service module):
`ProposalNotFoundError`, `ProposalNotOpenError`.
- [ ] **014.B1** Failing unit test (`backend/tests/test_approval.py`), fake repo + fixed `Clock`
      (`core/ports/clock.py`): `ApprovalService(repo, clock).approve(proposal_id, actor=..,
      notes=..)` on an OPEN proposal → calls `repo.resolve(id, to_state=APPROVED, reason=notes,
      resolved_at=clock.now())` **and** `repo.record_approval_event(id, actor=.., action="approve",
      notes=.., occurred_at=clock.now())`. Returns the resolved proposal (or a small result).
- [ ] **014.B2** Implement `ApprovalService.approve`: `p = repo.get(id)`; if `None` →
      raise `ProposalNotFoundError`; if `not p.state == OPEN` (use
      `proposal.py::is_valid_transition(p.state, APPROVED)`) → raise `ProposalNotOpenError`
      (record NO event); else resolve + record. Green. Commit.
- [ ] **014.B3** Failing tests: `reject(...)` → `REJECTED` + event `action="reject"`; **not-found**
      → `ProposalNotFoundError`; **already-terminal** (state ≠ OPEN) → `ProposalNotOpenError`, no
      `resolve`/`record` call.
- [ ] **014.B4** Implement `reject` + the guards (factor a shared `_decide(to_state, action, ..)`
      helper so approve/reject don't duplicate the load→guard→resolve→record sequence). Green.
      Commit.
- [ ] **014.B5** **Docstrings** (conventions checklist): module docstring + `ApprovalService`
      class + each public method, **citing dossier §12** (proposal lifecycle) **and §T1.1**
      (commit-first / best-effort side effects). Mirror peer services (`decide.py`,
      `ingest_service.py`). Commit.

### Phase C — composition: FastAPI app factory + provider/container
New `backend/src/composition/app.py` (or `api_app.py`). Composition is the only zone that may
import both core and adapters (dossier §4).
- [ ] **014.C1** Failing test (`backend/tests/test_app.py`, FastAPI `TestClient`):
      `GET /api/v1/health` → 200 with a small liveness body. The app is built by a `create_app(...)`
      factory that accepts injected dependencies (so tests inject a **fake** `ProposalRepository`;
      use FastAPI `app.dependency_overrides` or pass a container object into `create_app`).
- [ ] **014.C2** Implement: (a) `api/v1/health/` minimal feature (at least `controller.py` +
      `__init__.py`; a health route needs no DTO/validation/service logic — keep it honest but
      tiny; its existence makes the independence contract in Phase E non-vacuous). (b) `create_app`
      building the SQLAlchemy `Engine` from `Settings` (`composition/settings.py::load_settings`),
      constructing `PostgresProposalRepository(engine)` + a real `Clock`, wiring `ApprovalService`,
      and mounting the v1 router(s). Provide a FastAPI dependency that yields the `ApprovalService`
      so controllers/services resolve it without importing composition internals directly. Green.
      Commit.

### Phase D — api/v1/decisions five-file feature (TDD)
Directory `backend/src/api/v1/decisions/` with EXACTLY:
`__init__.py` (router re-export) · `controller.py` (routes/status codes, **no logic**) ·
`models.py` (pydantic HTTP DTOs only — NOT canonical domain types) · `validation.py` (syntactic
checks, **stdlib only**, no service imports) · `service.py` (**thin**: validate → call
`ApprovalService` via the injected dependency → shape the HTTP result; imports core + container,
**never another feature**).
- [ ] **014.D1** `models.py`: `DecisionRequest {action: str, actor: str, notes: str | None}`,
      `DecisionResponse {proposal_id: int, state: str, resolved_at: datetime}` (DTOs, not domain
      types). `validation.py`: `action ∈ {"approve","reject"}`, `actor` non-empty — raising a
      structured error the controller turns into **422**. Failing TestClient test: malformed body
      (missing `actor` / unknown `action`) → **422 BEFORE any core/DB call**.
- [ ] **014.D2** Failing TestClient tests (fake repo via `dependency_overrides`): approve OPEN →
      **200** + `state="approved"` + event recorded; reject OPEN → **200** + `state="rejected"`;
      unknown id → **404** (maps `ProposalNotFoundError`); already-terminal → **409** (maps
      `ProposalNotOpenError`).
- [ ] **014.D3** Implement `controller.py` (route `POST /api/v1/decisions/{proposal_id}`, body
      `DecisionRequest`; map domain errors → 404/409 via handlers or try/except in the thin edge
      service) + `service.py` (validate → `ApprovalService.approve|reject` → `DecisionResponse`).
      Green. Commit. Add module/class docstrings citing dossier §13.
- [ ] **014.D4** **AC5 (best-effort side effects, T1.1):** for this exemplar, publish-on-approve
      is **OUT OF SCOPE** — the decision endpoint commits the DB resolution (via
      `ApprovalService` → `repo.resolve`) and returns; no publish/notify is wired here. Add one
      test asserting the endpoint returns success purely from the repository commit (no publisher
      dependency). *(Rationale: the exemplar proves the five-file boundary + lifecycle mutation;
      wiring publish-on-approve belongs with the Publications work in STORY-014b. AC5 is satisfied
      in its reduced "commit-before-return" form — see the story AC5 note.)*

### Phase E — the 4th import-linter contract + DoD command-sync
- [ ] **014.E1** Add to `pyproject.toml` `[tool.importlinter]`:
      ```toml
      [[tool.importlinter.contracts]]
      name = "api-feature-independence"
      type = "independence"
      modules = ["src.api.v1.decisions", "src.api.v1.health"]
      ```
      (Mirrors the existing `adapters-independence` contract block, lines ~51-54.)
- [ ] **014.E2** Run `lint-imports` → must report **4 contracts kept, 0 broken**. Prove the
      contract is **not vacuous**: temporarily add `from src.api.v1 import health` inside
      `decisions/service.py`, confirm `lint-imports` now reports the new contract **BROKEN**, then
      revert. Record this spike in the story file History (AC2 evidence). *(import-linter
      `independence` with a 2-module list is non-vacuous; the health feature exists precisely so
      this list has ≥2 entries.)*
- [ ] **014.E3** **Command-sync (working-agreements.md 2026-06-23)** — in the SAME commit that
      lands the contract: update `.scrum/definition-of-done.md` (the `lint-imports` line: now
      enforces **four** dossier-§4 contracts — name the new one) AND `CLAUDE.md` (every place that
      says "3 contracts" / "three contracts" for `lint-imports` → four; the §4 description). No new
      gate COMMAND is added (lint-imports already runs), only the contract count changes. Commit.

### Phase F — wiki forward-blast-radius (DoD requirement)
- [ ] **014.F1** STORY-014's diff touches `pyproject.toml` (the import contracts) → matches
      `architecture-boundary.md`'s `code_refs`. That article is **verified** after STORY-034. Add a
      Fact for the 4th `api-feature-independence` contract (the dossier-§13 no-horizontal-feature
      rule), using symbol/section citation form, and bump its `verified_sha` to current HEAD +
      `verified_sprint: sprint-12`. Confirm `api/__init__.py` + `pyproject.toml` (already in its
      `code_refs`) still cover the new Facts.
- [ ] **014.F2** (Optional, may defer to the sprint-end compile pass) seed a short
      `api-five-file-convention.md` wiki article (`code_refs`: the `api/v1/decisions/*` files +
      `composition/app.py` + `pyproject.toml`) capturing the convention + the 4th contract. If
      skipped here, the orchestrator handles it in the blocking compile pass before review.

### Phase G — full gate
- [ ] **014.G** All SIX DoD commands exit 0 (spin up the throwaway DB for FK/alembic/DB-gated
      pytest). No new migration expected (proposals + approval-events tables exist from STORY-012;
      only a port METHOD was added). If `alembic upgrade head` or `check_fk_direction.py` reveals a
      genuine schema need, STOP and raise it — do not invent a migration outside the AC.

**AC mapping:** AC1 ← Phase D shape; AC2 ← Phase E; AC3 ← Phases B+D + core-independence KEPT;
AC4 ← 014.D1-D3; AC5 ← 014.D4 (reduced form); AC6 ← Phase G + Phase F.

---

## Standing conventions checklist (binds all new code — working-agreements.md 2026-06-27)
- [ ] Module + public class/function **docstrings citing the relevant dossier §** (peers:
      `ingest_service.py`, `pipeline.py`, `decide.py`, `status.py`, `proposal.py`).
- [ ] New frozen value/result DTOs enforce any cross-field coherence invariant with a
      `model_validator(mode="after")` + a test of both the rejected and valid shapes.
- [ ] Empty-input / edge behavior tested for every new port-touching method (the 404/409/422
      paths are these for the decision endpoint; `get` not-found → `None` for the port).
- [ ] A port's fake and its real adapter AGREE on edge behavior (run the same not-found contract
      against both — working-agreements.md 2026-06-26).
- [ ] Parallel-shape logic shares one assembly helper (the approve/reject `_decide` helper —
      working-agreements.md 2026-06-25).
- [ ] Scoped staging (never `git add -A`); follow existing import/naming/structure patterns.
- [ ] If a story changes a build/test/run command or the architecture boundary: CLAUDE.md +
      `.scrum/definition-of-done.md` updated in the SAME commit (command-sync).

## Notes / risks
- STORY-014 at 5 is meaty (3 zones). If a phase balloons past ~3× its share, mark the story
  Blocked with the specific obstacle rather than guessing (effort cap / blocked protocol).
- No tooling/MCP change this sprint. The only dependency move is confirming fastapi + httpx
  (014.0), a normal library add.
