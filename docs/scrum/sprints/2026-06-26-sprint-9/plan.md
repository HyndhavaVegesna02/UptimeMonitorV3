# Sprint 9 — Plan (implemented externally by the PO / Gemini)

**Goal:** Zone 5's two foundations — the proposal substrate (STORY-012) and the Statuspage publish
adapter (STORY-013) — setting up `decide` (STORY-024) to tie them together next.

**Branch:** `sprint-9` · **Start tag:** `sprint-9-start` · **Started:** 2026-06-26
**Capacity:** 6 · **Committed:** 6 (STORY-012 = 3, STORY-013 = 3)
**Order:** STORY-012 first, then STORY-013 (independent; either order works).

## How this sprint runs (workflow change)
The PO implements these stories externally (Antigravity / Gemini), committing onto `sprint-9`. Build
to the AC + the TDD steps below. Then the PO tells the orchestrator "do your review", and the
orchestrator runs the full DoD gate + spec/quality reviews (Opus) + the wiki blast radius + merge.

**A story is Done only when ALL FOUR DoD commands exit 0 AND both reviews pass:**
- `.venv/Scripts/python.exe -m pytest` → 0
- `.venv/Scripts/lint-imports.exe` → 0 (`3 kept, 0 broken`)
- `.venv/Scripts/python.exe scripts/check_fk_direction.py` → 0  (DB-gated)
- `.venv/Scripts/alembic.exe upgrade head` → 0  (DB-gated; NO new migration this sprint)

DB-gated commands need a throwaway Postgres: `.venv/Scripts/python.exe scripts/dev_db.py up` (prints
two `export DATABASE_URL...` lines; `down` to tear down). Requires Docker Desktop running. If `up`
errors "port 55432 address already in use", run `docker rm -f uptime_pg_pytest` then retry.

**Standing working agreements (all apply):** boundary = build failure (`lint-imports` 3 kept); pure
core / mockable edges (in-memory fakes for unit tests, only the Postgres adapter is DB-gated);
**empty-input behavior tested**; **range/boundary tested** (non-aligned cases); **frozen value/result
types MUST enforce cross-field coherence invariants with a `model_validator(mode="after")` + a test**;
**every wiki Fact's cited file must be in the article's `code_refs`**; scoped staging (never
`git add -A`); commit per green TDD step; CLAUDE.md only if a command/stack changes (none expected).

---

## STORY-012 — Proposal substrate: types + state machine + repository (3 pts)

Spec: dossier §12 + §9. Story file: `docs/scrum/stories/STORY-012-proposal-lifecycle.md` (read it).
**The reconciliation RULE is OUT OF SCOPE (STORY-024).** Build only types + state machine + port +
Postgres adapter. NO new migration — the tables already exist (STORY-006).

Existing schema to target (`migrations/versions/3a8254bcfe59_spine_schema.py`):
- `status_proposals(id bigserial pk, component_id text FK→components RESTRICT, from_status text NULL,
  to_status text NOT NULL, state text NOT NULL, reason text NULL, proposed_at timestamptz,
  resolved_at timestamptz NULL, created_at timestamptz)`; `state` CHECK ∈ {open, approved, rejected,
  superseded, obsoleted}; partial-unique `uq_status_proposals_active_component` ON (component_id)
  WHERE `state='open'`. `to_status`/`from_status` CHECK ∈ the 4 ComponentStatus values.
- `approval_events(id, proposal_id FK→status_proposals CASCADE, actor text, action text, notes text
  NULL, occurred_at timestamptz)`; `action` CHECK ∈ {approved, rejected}.

Read first: `backend/src/core/domain/status.py` (`ComponentStatus`, frozen-Pydantic style + the new
`Verdict`/`AntiFlapOutcome` validators for the coherence pattern), `backend/src/core/ports/
observation_repository.py` + `watermark.py` (ABC port style), `backend/src/adapters/persistence/
observation_repository.py` (injected `Engine`, `sa.table`, `pg_insert(...).on_conflict_do_nothing()`,
no globals), `backend/tests/test_persistence_adapters.py` (the `migrated_db` + `engine` DB-gated
pattern; note `status_proposals.component_id` FKs into `components` — seed a parent `apps`+`components`
row in the test as that file already does for `signals`).

TDD steps (commit after every green step):
- [ ] 1. Domain: add `ProposalState` enum (open/approved/rejected/superseded/obsoleted) + a frozen
        `StatusProposal` type in `core/domain/` (export from `core/domain/__init__.py`). Failing test
        → construct a valid open + a valid terminal proposal. Commit.
- [ ] 2. Domain coherence invariant (sprint-8 agreement): a `model_validator(mode="after")` enforcing
        `resolved_at is None` IFF `state == open` (open ⇒ no resolved_at; terminal ⇒ resolved_at set).
        Failing tests: both incoherent shapes raise; both valid shapes construct. Implement. Commit.
- [ ] 3. Domain transition rule: a helper (e.g. `StatusProposal.terminal` property / a
        `is_valid_transition(from_state, to_state)` function) — `open` → any terminal; terminal → none.
        Failing tests at the boundaries (open→approved ok; approved→rejected rejected; open→open
        rejected). Implement. Commit.
- [ ] 4. Port: `ProposalRepository` ABC in `core/ports/` with `create_open(proposal) ->
        StatusProposal | None`, `get_open(component_id) -> StatusProposal | None`,
        `resolve(proposal_id, *, to_state, reason, resolved_at) -> None`, `record_approval_event(
        proposal_id, *, actor, action, notes, occurred_at) -> None`. Export it. Add a list/dict-backed
        fake to `backend/tests/fakes.py` (its `create_open` honors one-open-per-component, returning
        `None` on a second open). Failing test via the fake. `lint-imports` green. Commit.
- [ ] 5. Adapter: `PostgresProposalRepository(engine)` in `adapters/persistence/proposal_repository.py`.
        `create_open` = `pg_insert(...).on_conflict_do_nothing()` against the partial-unique, RETURNING
        — if no row returned (a concurrent open exists), log a `logging` debug line and return `None`.
        Failing DB-gated test (`migrated_db`): two `create_open` for one component → first persists,
        second returns `None`, only one open row exists. Commit. (AC3)
- [ ] 6. Adapter: `get_open` (SELECT the open row), `resolve` (UPDATE state+resolved_at+reason of the
        open row to a terminal), `record_approval_event` (INSERT approval_events). Failing DB-gated
        tests: get_open returns it; after `resolve` a NEW `create_open` succeeds (the old one freed the
        partial-unique); approval_event row written. Commit. (AC4)
- [ ] 7. Self-review (pure core imports only `src.core.*`; all SQL in the adapter; no globals). Commit.
- [ ] 8. DoD gate (all four exit 0). Forward blast radius: update `canonical-types-and-ports.md`
        (adds a domain type + a port → Facts + `verified_sha`) and `persistence-adapters.md` (adds the
        adapter → Facts + `verified_sha`). Commit.

---

## STORY-013 — Statuspage publish adapter + commit-first boundary (3 pts)

Spec: dossier §6 + §12 + §14 T1.1. Story file: `docs/scrum/stories/STORY-013-statuspage-publish-adapter.md`.
First `adapters/outbound/` implementation. NO live Statuspage / HTTP — an injected executor seam +
recorded fixtures, mirroring the Dynatrace adapter's `Executor`.

Read first: `backend/src/core/ports/status_publisher.py` (`StatusPublisherPort.publish(change:
StatusChange) -> None`), `backend/src/core/domain/status.py` (`StatusChange{component_id, status:
ComponentStatus}`, frozen), and `backend/src/adapters/inbound/dynatrace/query.py` (the `Executor =
Callable[...]` injected-seam pattern) + `adapter.py` (how the seam is wired) + `dynatrace/__init__.py`
(package style). The composition zone (`backend/src/composition/`) may import both core + adapters.

TDD steps (commit after every green step):
- [ ] 1. Package `adapters/outbound/statuspage/__init__.py` + an `Executor`-style seam type (a
        `Callable` for the HTTP call — faked in tests). Author recorded request/response fixtures under
        `backend/tests/fixtures/statuspage/`. Failing test scaffolding; `pytest` + `lint-imports` green.
        Commit.
- [ ] 2. Failing test: the adapter maps `ComponentStatus` → the Statuspage component-status string
        (define the explicit mapping: operational/degraded/partial_outage/major_outage → the vendor's
        values) — exhaustive over the closed enum, raises on an unmapped value (like the dynatrace
        health mapping). Implement the status mapping. Commit. (AC1)
- [ ] 3. Failing test: `StatuspagePublisher(StatusPublisherPort)` `.publish(change)` resolves
        `component_id` → vendor id via an INJECTED mapping (a dict/resolver passed to the constructor),
        builds the request (asserted against the fixture), and calls the injected executor. A
        `component_id` with no mapping raises a clear named error. Implement. Commit. (AC1/AC4)
- [ ] 4. Composition: `publish_best_effort(publisher, change, *, logger)` in `backend/src/composition/`
        — calls `publisher.publish(change)` in a `try/except`, logs on failure, returns normally (never
        re-raises). Failing test: a raising fake publisher → no exception escapes + the failure is
        logged (assert via `caplog`). Implement. Commit. (AC2)
- [ ] 5. Self-review: adapter under `adapters/outbound/statuspage/` only; no vendor id/type in core;
        the best-effort helper in `composition/`; `lint-imports` green (no adapter→adapter import).
        Commit.
- [ ] 6. DoD gate (all four exit 0; no migration). Forward blast radius: the publish path is new —
        create a wiki article (e.g. `statuspage-publish.md`) for it with `code_refs` covering
        `adapters/outbound/statuspage/` + the composition helper + the test, OR fold into an existing
        article IF its code_refs cover the new files (per the sprint-7 agreement, every Fact's cited
        file must be code_ref-covered). Commit.

---

## Reviews (orchestrator, after the PO says "do your review")
Per story (both 3 pts → full pipeline): spec reviewer (Opus) vs the AC verbatim, then code-quality
reviewer (Opus), then the mechanical DoD gate re-run by the orchestrator. Fix-loop findings route
back to the PO/Gemini (default) unless the PO asks the orchestrator to fix inline.
