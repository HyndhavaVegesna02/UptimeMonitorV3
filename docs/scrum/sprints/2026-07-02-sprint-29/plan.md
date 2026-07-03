# Sprint 29 — Plan

**Dates:** starts 2026-07-02.
**Goal:** close the approve→publish→write-back dead end (STORY-045) — the product's core loop.
**Branch:** `sprint-29` (tag `sprint-29-start` @ `162783d`). Committed: 5 pts (velocity mean 4.3;
the Sprint-28 "3" was a deliberate under-commit — 25–27 each delivered 5/5; PO approved).
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers
(5 pts → full pipeline).

This is a BACKEND story. Work is under `backend/src/core/` (ports, services, domain),
`backend/src/adapters/persistence/`, `backend/src/composition/`, and tests under
`backend/tests/`. **No frontend change. No new API feature module** (the existing
`POST /api/v1/decisions/{proposal_id}` endpoint is the trigger; its five files change only where
stated). The six backend DoD commands must stay green.

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green
step**, staging only touched files (never `git add -A`), branch verified `sprint-29` before each
commit. DB-gated tests use the shared `migrated_db` fixture; NEVER run two DB-gated pytest
invocations concurrently against one throwaway DB (2026-07-02 agreement).

## Key facts (verified against code, 2026-07-02)

- `core/services/approval.py::ApprovalService` — constructed with ONLY `proposal_repo` + `clock`;
  `approve()`/`reject()` → `_decide()` does: get → guard (`is_valid_transition`) → `resolve` →
  `record_approval_event` → re-`get` → return. NO publisher, NO status write.
- `core/services/decide.py::DecideService.decide` — recovery branch (`proposed_is_better`) builds
  `StatusChange(component_id, status)` and calls `self._publisher.publish(change)` LAST, after all
  repo writes (commit-first). Degradations never publish. `DecideService` itself stays pure — its
  injected `publisher` is whatever chain composition wires.
- `core/ports/component_repository.py::ComponentRepository` — ABC with `list_components` + `get`
  only. `adapters/persistence/component_repository.py::PostgresComponentRepository` — SELECTs only,
  no UPDATE. The fake lives in `backend/tests/` (find it via `grep -r "class Fake.*ComponentRepo"
  backend/tests/`); parity agreement 2026-06-26 applies.
- `core/domain/component.py::Component` — frozen Pydantic read model `{id, name, status, app_id}`.
  There is currently NO component-scoped domain error; proposal errors live in
  `core/domain/proposal.py` (`ProposalNotFoundError` pattern to mirror).
- `composition/publish_helper.py` — `BestEffortPublisher(delegate)` (swallows+logs),
  `RecordingPublisher(delegate, publication_repo, clock)` (records a `Publication` ONLY on delegate
  success — dossier §12/T1.1, keep), `LoggingPublisher()` (no-creds fallback).
- `composition/run.py::build_live_loop` — assembles, IF statuspage secrets + mapping present:
  `BestEffortPublisher(delegate=RecordingPublisher(delegate=StatuspagePublisher(...), ...))`,
  ELSE `LoggingPublisher()`; injects into `DecideService`.
- `composition/app.py::create_app` — the API-process composition root. Wires repos (real or
  injected fakes), `clock`, and `ApprovalService(proposal_repo, clock)` into `app.state`. It has
  `publication_repo` but NO publisher and NO Statuspage wiring. **The approve endpoint runs in THIS
  process**, so the publisher chain must exist here too.
- `composition/settings.py::load_live_secrets` — requires the DYNATRACE vars (raises
  `MissingLiveSecretError` without them) — create_app must NOT call it just to get the two optional
  statuspage vars; read `STATUSPAGE_PAGE_ID` / `STATUSPAGE_API_KEY` (and the config mapping)
  the way `LiveSecrets` names them, tolerating absence (fallback = LoggingPublisher). Verify how
  `LiveSecrets` models optional statuspage fields and reuse that, don't invent a second convention.
- `api/v1/decisions/service.py::get_decision_service` → `get_approval_service` (in
  `api/dependencies.py`) resolves `app.state.approval_service`. Error mapping 404/409 exists;
  don't change it.
- `composition/orchestrate.py::orchestrate_signal` step 5 reads
  `component_repo.get(component_id)` → passes `current_status` into `decide`. Unchanged by this
  story — it starts WORKING (varying) once write-back lands.

## Design decisions (pinned — do not improvise; 2026-06-26 plan-edge-behavior agreement)

**D1 — Write-back is a composition-layer publisher decorator, applied at BOTH roots.**
New `StatusWritebackPublisher(delegate, component_repo)` in `composition/publish_helper.py`:
`publish(change)` writes `component_repo.set_status(change.component_id, change.status)` FIRST,
then calls `delegate.publish(change)`. Rationale: both trigger points (approve in the API process,
recovery in the loop process) publish through a chain, so one decorator gives write-back at both
with zero change to `DecideService`. The write-back is a durable DB write and belongs BEFORE the
external call (commit-first, §T1.1) and OUTSIDE `BestEffortPublisher` — a write-back failure is a
DB failure and must PROPAGATE (it is not "best effort"); only the external Statuspage call is
swallowed. A write-back for an unknown component id raises the D3 domain error and propagates
(it means the topology seed and the change disagree — loud, never swallowed).

**D2 — Full chain shape (both composition roots, via ONE shared assembly helper).**
`composition/publish_helper.py` (or a sibling composition module) gains a shared builder, e.g.
`build_publisher(*, component_repo, publication_repo, clock, statuspage_page_id, statuspage_api_token,
component_mapping) -> StatusPublisherPort`, returning:
  - creds+mapping present: `StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(
    StatuspagePublisher(...))), component_repo)`
  - else: `StatusWritebackPublisher(LoggingPublisher(), component_repo)`
`run.py` REFACTORS its inline block to call this helper (share-the-assembly agreement 2026-06-25 —
two roots assembling the same chain is exactly the drift the agreement targets); `create_app` calls
it too. NOTE the write-back applies on the LoggingPublisher path as well — the local no-creds dev
stack must see the Dashboard change (memory: local dev exists to SEE live results).
Publication-recording semantics UNCHANGED: a `publications` row only on Statuspage success.
Net ordering per trigger: proposal writes → status write-back → best-effort external publish →
record publication on success. A Statuspage outage loses NOTHING durable (AC4).

**D3 — Port method + named domain error.**
`ComponentRepository.set_status(component_id: str, status: ComponentStatus) -> None` (abstract).
New `ComponentNotFoundError` in `core/domain/component.py` (mirror
`core/domain/proposal.py::ProposalNotFoundError` style; export via the domain/ports `__init__`s the
way peers are). Postgres adapter: `UPDATE components SET status=... WHERE id=...`; `rowcount == 0`
→ raise `ComponentNotFoundError` (never a bare ValueError — 2026-06-28 check-then-act agreement).
Fake: IDENTICAL behavior. ONE contract test parametrized/shared across BOTH implementations
(Postgres side DB-gated via `migrated_db`) proving: known id updates + persists; unknown id raises
`ComponentNotFoundError` in both (2026-06-26 parity agreement).

**D4 — `ApprovalService` gains a REQUIRED `publisher: StatusPublisherPort` kwarg.**
On `approve()`, AFTER `resolve` + `record_approval_event` (commit-first), build
`StatusChange(component_id=proposal.component_id, status=proposal.to_status)` and
`self._publisher.publish(change)`. `reject()` publishes NOTHING (tested). Do NOT make the kwarg
optional/defaulted — a silently-unwired publisher is this very defect again; all constructors are
in `create_app` + tests, update them (a contract change REWRITES its tests — 2026-06-29 agreement).
The publisher injected in production is the D2 chain, so approve's write-back + best-effort
semantics come from the chain, not from ApprovalService logic (keep the core service thin; it
publishes, the chain does the rest — same division as decide).

**D5 — What explicitly does NOT change.**
`DecideService` (no code change — its publisher just gets the richer chain), `orchestrate.py`,
the seed (still never touches runtime status at upsert), the API surface (no new endpoints/DTOs),
the frontend, `alembic` (no schema change — `components.status` column exists).

## STORY-045 — approve→publish→write-back (5 pts) — AC1–AC6

- [x] **T1 — Port + parity (AC3), TDD.** Failing contract test first: shared test exercising
      `set_status` against BOTH the fake and `PostgresComponentRepository` (DB-gated half via
      `migrated_db` + seeded component; keep it ONE test body applied to both impls). Assert:
      update visible via `get`/`list_components`; unknown id → `ComponentNotFoundError` from BOTH.
      Then: add `ComponentNotFoundError` (domain), the abstract `set_status`, the Postgres UPDATE
      (rowcount guard), and the fake's identical impl. Commit per green step.
- [x] **T2 — `StatusWritebackPublisher` + shared `build_publisher` (D1, D2), TDD.** Failing tests
      first: (a) writeback publisher writes status THEN delegates (order observable via a spy
      delegate that reads the fake repo's status when called); (b) delegate failure inside
      BestEffort does NOT prevent the already-done write-back, and nothing is recorded in
      publications (compose the real chain with fakes — do NOT patch `__init__`s of the things
      under assembly, 2026-06-29 composition-test agreement); (c) unknown-component write-back
      propagates `ComponentNotFoundError`; (d) `build_publisher` returns the D2 shapes for
      creds-present vs absent (assert `isinstance` nesting / `_delegate` refs — the real wiring).
      Then implement; REFACTOR `run.py::build_live_loop` to consume `build_publisher` (behavior
      identical; its existing wiring tests keep passing or are UPDATED, never deleted).
- [x] **T3 — Approve publishes (AC1, D4), TDD.** Failing tests first, against `ApprovalService`
      with fake repo/clock + a fake publisher: approve → publisher received exactly one
      `StatusChange(component_id, to_status)` AFTER resolution (assert proposal already resolved
      when publish observed, or at minimum ordering via call recording); reject → zero publishes;
      the existing 404/409 guard paths still publish nothing. Then add the required `publisher`
      kwarg + the publish call; update `create_app` to build the D2 chain (real path: engine-backed
      component/publication repos + env statuspage creds via the existing settings shapes;
      injected-fakes path: tests supply what they need — keep the injection surface symmetric with
      the existing repo params, e.g. accept an optional `publisher=` override for tests) and update
      every existing `ApprovalService(...)`/`create_app(...)` construction the suite already has.
      The decisions-endpoint tests gain: approve via HTTP → publication recorded + status written
      (fakes injected through `create_app`).
- [x] **T4 — Write-back at both trigger points (AC2) + recovery reachability (AC5), TDD.**
      (a) Approval trigger: after an approve through the D2 chain (fake Statuspage delegate),
      `components.status` == to_status and `GET /api/v1/components` serves it (TestClient with
      injected fakes or DB-gated — implementer's choice, cheapest honest path).
      (b) Recovery trigger: a `DecideService` wired with the chain publishing a recovery →
      status written back.
      (c) AC5 end-to-end orchestration regression: drive degrade → approve → recover through
      `orchestrate_signal` + `ApprovalService` (fake observation data shaped like the existing
      orchestrator tests): cycle 1 degradation → proposal opened, nothing published, status
      unchanged; approve → publish observed + publications row + status now degraded; cycle 2 UP
      observations → decide's recovery branch fires (`PUBLISHED_RECOVERY`) → recovery publish +
      status back to operational. This asserts the previously-unreachable branch is now reachable.
- [ ] **T5 — Gates + docs + blast radius (AC6).** All six backend DoD commands exit 0 on a clean
      committed tree — SINGLE non-concurrent DB-gated run. CLAUDE.md: no command changes expected
      (command-sync N/A unless you add one). Wiki blast radius: your diff will touch `code_refs` of
      at least `statuspage-publish`, `core-pipeline-and-availability`, `api-five-file-convention`
      (approvals/decisions wiring), `architecture-boundary` (only if pyproject/zone roots move —
      avoid), `dev-setup-and-dod` (only if commands change). Update the affected articles' Facts in
      the same story (symbol-cited, 2026-06-27 agreement) and REPORT which you touched; the
      orchestrator runs the mechanical sweep at the compile pass.

## Conventions checklist (held at quality review)
- Module + public-symbol docstrings citing the relevant dossier § (peers: `approval.py`,
  `decide.py`, `publish_helper.py` set the register). New port method + error get the same
  treatment (parity-agreement citation in the docstring like `get`'s).
- Frozen value/result types: none new expected; if you add one with a cross-field invariant,
  `model_validator(mode="after")` + both-shapes tests (2026-06-26).
- Empty-input + non-aligned-boundary tests where applicable (2026-06-25) — mostly N/A here; the
  AC5 e2e must not use only clean-multiple windows if it computes windows.
- Composition/assembly tests construct REAL wired objects; mock only genuine I/O edges (the
  Statuspage HTTP executor, the DB engine where faked) — never the `__init__` of a thing whose
  wiring is asserted (2026-06-29).
- A contract change REWRITES covering tests (constructor signature changes: `ApprovalService`,
  possibly `create_app`) — never deletes them to a gap (2026-06-29).
- Named domain errors, never bare `ValueError` on 0-row conditional writes (2026-06-28).
- Fake/adapter parity incl. the new `set_status` (2026-06-26).
- Scoped staging; commit-after-green; no `git add -A`; ruff-clean before each commit.
- Import boundaries: the decorator + builder live in `composition` (may import core + adapters);
  core gains NO outward import; `lint-imports` stays 5 kept / 0 broken.

## Guardrails (implementer)
- Build to THIS plan + `docs/scrum/stories/STORY-045-approve-publish-status-writeback.md` + dossier
  §10/§12/§14-T1.1/§17 — never chat history. The D1–D5 decisions are BINDING; genuine conflict
  between them and the code you find → STOP and report, don't improvise.
- Do NOT write `.scrum/` board state; do NOT run reviewers or merge — the orchestrator owns the
  back half. No live credentials needed anywhere (fakes + throwaway DB prove everything).
- Genuine ambiguity → STOP with the exact question. Effort > 3× the 5-pt estimate → STOP.
- Report: steps done + commit SHA each; every gate command + exit code + output tail; which wiki
  articles your diff touches (with what you updated); net-new/rewritten/deleted tests with the
  justification; anything noticed-but-not-done.

## Sequencing rationale
T1 first — the port method is the foundation everything else calls, and its parity contract is the
riskiest boundary. T2 builds the chain on top of it (pure composition, fake-testable). T3 threads
the publisher into the approve path (the headline defect). T4 proves both trigger points and the
recovery branch end-to-end (AC5 is the story's reason-to-exist regression). T5 gates + wiki. Risk
lives in the two composition roots agreeing on one chain (D2's shared builder addresses it) and in
constructor-signature ripple through the existing suite (D4 names the rewrite obligation).
