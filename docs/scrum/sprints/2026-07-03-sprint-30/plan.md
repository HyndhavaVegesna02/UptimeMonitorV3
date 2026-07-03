# Sprint 30 — Plan

**Dates:** starts 2026-07-03.
**Goal:** expose the topology + component-grain availability the frontend is blind to (STORY-044)
— component→signals enumeration, rollup-plus-children availability, authoritative server-side
per-signal intervals (kills audit H2's 60-vs-120 completeness mis-compute). Unblocks STORY-015d
and STORY-015e.
**Branch:** `sprint-30` (tag `sprint-30-start` @ `f9d160c`). Committed: 5 pts (velocity mean 4.3;
same single-5 shape the PO approved for sprints 25–27 and 29 — all delivered 5/5; PO approved:
"lock story 044", 2026-07-03).
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers
(5 pts → full pipeline).

This is a BACKEND story. Work is under `migrations/versions/`, `backend/src/core/` (domain,
ports), `backend/src/adapters/persistence/`, `backend/src/composition/` (seed + app wiring),
`backend/src/api/` (one NEW five-file module + the existing availability module), and tests under
`backend/tests/`. **No frontend change. No change to the core calculator/pipeline** (`rollup_group`
already exists and is consumed as-is). The six backend DoD commands must stay green.

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green
step**, staging only touched files (never `git add -A`), branch verified `sprint-30` before each
commit. DB-gated tests use the shared `migrated_db` fixture; NEVER run two DB-gated pytest
invocations concurrently against one throwaway DB (2026-07-02 agreement).

## Key facts (verified against code, 2026-07-03)

- **`signals` has NO `interval_seconds` column.** Spine migration `3a8254bcfe59` + follow-up
  `eec78d2e8cbe` (current head; new revision chains from it) give `signals`:
  `signal_key PK, app_id, name, component_id (nullable, FK→components ON DELETE SET NULL),
  updated_at`. `composition/config.py::SignalConfig.interval_seconds` EXISTS (int > 0, validated)
  and `config/apps/httpcheck.yaml` says `interval_seconds: 120` — but `composition/seed.py`
  never persists it (its `_SIGNALS` lightweight `sa.table` lists no such column).
- `composition/seed.py::seed_topology(config, engine)` — idempotent upsert apps → components →
  signals inside one `engine.begin()`; per-table `on_conflict_do_update` with explicit `set_`.
  Runs at API boot via `composition/app.py::lifespan` when `app.state.seed_config` + `db_engine`
  are set, and from `run.py`. Tests: `backend/tests/test_seed.py` (DB-gated, `migrated_db`).
- `core/services/availability.py` — `AvailabilityCalculator(observation_repo=...)` with
  `.compute(signal_key, *, since, until, interval: timedelta, window: str, maintenance, computed_at)
  -> AvailabilityResult`; and **`rollup_group(children: Sequence[AvailabilityResult], *, window,
  computed_at) -> AvailabilityResult`** — MIN over non-None percentages, counts SUM,
  `distinct_locations=0` for a synthesized rollup. `rollup_group([])` yields the all-None/0
  degenerate result and passes `AvailabilityResult`'s validator. DO NOT MODIFY this module.
- `api/v1/availability/` — `controller.py` has `_DEFAULT_INTERVAL_SECONDS = 60` and the STALE
  param description "stopgap default 60; STORY-040 will supply per-signal config" (STORY-040
  closed sprint 18 without doing it — that lie is audit H2). `service.py::AvailabilityService`
  is constructed `(observation_repo, clock)`; `get_availability(signal_key, *, since_str,
  until_str, interval_seconds)` defaults `until=clock.now()`, `since=until−24h`, window label
  `"24h"` or `"{since}..{until}"` ISO pair; maintenance predicate is a documented no-op stopgap.
  `validation.py::validate_availability_request` enforces non-empty signal_key, parseable +
  **tz-aware** since/until (422), positive interval. Existing endpoint tests:
  `backend/tests/test_availability_endpoint.py` (fake-injected via `create_app`).
- `core/ports/component_repository.py::ComponentRepository.get(component_id) -> Component | None`
  — returns `None` on unknown, never raises. `ComponentNotFoundError` already exists in
  `core/domain/component.py` (STORY-045). `Component` is frozen `{id, name, status, app_id}`.
- `composition/app.py::create_app` — injection pattern: optional repo kwargs; the
  `proposal_repo is None` branch builds ALL real Postgres repos from one engine + loads config
  into `app.state.seed_config`; the injected branch leaves others as-passed. Everything lands on
  `app.state.<name>`; `api/dependencies.py` has one `get_<name>` provider per port reading
  `request.app.state.<name>`. Mirror this exactly for the new signal repo.
- `api/v1/__init__.py` — flat `include_router` list; add the new topology router there.
- Five-file convention: every `api/v1/<feature>/` is EXACTLY
  `{__init__, controller, models, validation, service}.py` with a set-equality shape test
  (mirror `test_components_endpoint.py::test_components_module_five_file_shape`); DTOs are
  frozen Pydantic; DI provider lives in the feature's `service.py`; controller stays import-clean
  (wiki: `api-five-file-convention.md`).
- Fakes live in `backend/tests/` (find via `grep -r "class Fake" backend/tests/` — mirror
  `FakeComponentRepository`'s home and style). Parity agreement 2026-06-26 applies to any new
  port.

## Design decisions (pinned — do not improvise; 2026-06-26 plan-edge-behavior agreement)

**D1 — Schema: `signals.interval_seconds` is a NULLABLE Integer column, backfilled by the boot
seed.** New Alembic revision (down_revision `eec78d2e8cbe`):
`op.add_column("signals", sa.Column("interval_seconds", sa.Integer(), nullable=True))`; downgrade
drops it. Nullable because a migration cannot read `config/` (config is composition's job) and
must not invent a default — the seed is the backfill: `seed_topology` adds `interval_seconds` to
the `_SIGNALS` table def, the insert values, and the conflict `set_`, so the first boot after
upgrade populates every configured signal. No FK, no spine-direction change —
`check_fk_direction.py` unaffected. A NULL that somehow survives (seed never ran) is surfaced
honestly by D2/D6, never guessed around.

**D2 — New domain type + port, `None`-on-unknown parity with `ComponentRepository.get`.**
`core/domain/topology.py`:
- `class Signal` — frozen Pydantic `{signal_key: str, name: str, component_id: str | None,
  interval_seconds: int | None}`. `model_validator(mode="after")`: `interval_seconds` must be
  `> 0` when not None (2026-06-26 coherence agreement; both-shapes tests). Docstring cites
  dossier §7/§9 (seeded topology read model) and distinguishes it from
  `core/domain/signal.py::SignalObservation` (runtime observation vs seeded topology row).
- `class SignalNotFoundError(Exception)` — raised by the EDGE SERVICE (not the port) when the
  default-interval path needs a signal that isn't in the topology.
- `class SignalIntervalUnconfiguredError(Exception)` — signal row exists but
  `interval_seconds IS NULL` (seed predates D1 or never ran). Distinct from not-found: the
  remedy is "re-seed", not "wrong key".
Export all three via `core/domain/__init__.py`.
`core/ports/signal_repository.py::SignalRepository(ABC)`:
- `list_signals() -> list[Signal]` — ALL seeded signals ordered by `signal_key` (deterministic);
  `[]` when none exist. Never raises.
- `get(signal_key: str) -> Signal | None` — `None` on unknown; never raises, never a sentinel
  (mirror `ComponentRepository.get`, 2026-06-26 parity agreement).
Export via `core/ports/__init__.py`.
`adapters/persistence/signal_repository.py::PostgresSignalRepository(engine)` — SELECTs only,
mirroring `PostgresComponentRepository`'s style. Fake in `backend/tests/` mirrors peers. ONE
parity contract test body applied to BOTH implementations (Postgres half DB-gated via
`migrated_db` + seeding): empty → `[]`; ordering by signal_key; `get` unknown → `None`; `get`
known → all four fields incl. a NULL interval surfacing as `None`.

**D3 — AC1 endpoint = NEW five-file module `api/v1/topology/`, GET `/topology`.**
Response: `list[ComponentTopologyDTO]` — one entry per component from
`ComponentRepository.list_components()` (that order), each
`{id: str, name: str, signals: list[TopologySignalDTO]}` with signals grouped from
`SignalRepository.list_signals()` by `component_id`, sorted by `signal_key`.
`TopologySignalDTO = {signal_key: str, name: str, interval_seconds: int | None,
component_id: str}` (the AC names component_id per-signal; inside a component group it is that
component's id). Both DTOs frozen. Edge behaviors: empty topology → 200 `[]`; component with
zero signals → entry with `signals: []`; an orphan signal (`component_id` NULL, or referencing
no listed component) appears NOWHERE in the nesting — AC1 is component-centric; document this in
the module docstring (config validation already rejects dangling component_ids at load, so only
NULL is reachable in practice). No query params → `validation.py` mirrors the trivial-validator
pattern of the components feature. Status/availability are NOT in this payload (the Dashboard
has /components; 015d calls the D5 endpoint). Five-file shape test is a NAMED deliverable
(2026-06-28 agreement). Wiring: `signal_repo` param on `create_app` (symmetric with
`component_repo`: real branch builds `PostgresSignalRepository(engine)` when None; injected
branch leaves as-passed), `app.state.signal_repo`, `get_signal_repo` in `api/dependencies.py`,
router registered in `api/v1/__init__.py`. Tests: fake-injected (empty → `[]`, multi-signal
nesting, zero-signal component, orphan exclusion) + ONE DB-gated test seeding a multi-signal
config through `seed_topology` and asserting the full payload incl. `interval_seconds` (AC1
demands "sourced from the seeded topology" — the DB-gated test is the proof; nothing reads
`config/` at request time).

**D4 — AC2 endpoint = GET `/availability/component/{component_id}` in the EXISTING availability
module.** Query params `since`/`until` (optional, same defaulting + window label as the
per-signal endpoint — factor the window-resolution into ONE shared private helper inside
`service.py` rather than duplicating it, 2026-06-25 share-the-assembly agreement). NO
interval param — each child uses ITS OWN configured interval.
`AvailabilityService` gains `component_repo: ComponentRepository` + `signal_repo:
SignalRepository` ctor deps (contract change → REWRITE every construction/provider call site,
2026-06-29 agreement; `get_availability_service` resolves them via the existing
`get_component_repo` + new `get_signal_repo` providers).
`get_component_availability(component_id, *, since_str, until_str) -> ComponentAvailabilityDTO`:
1. `component_repo.get(component_id)` → `None` → raise `ComponentNotFoundError` → controller
   maps to **404**.
2. children = signals with `component_id == <id>` from `list_signals()` (sorted by signal_key);
   any child with `interval_seconds is None` → raise `SignalIntervalUnconfiguredError` →
   controller maps to **409** (forced via fake in a test; unreachable once seeded).
3. per child: `AvailabilityCalculator.compute(child.signal_key, since=…, until=…,
   interval=timedelta(seconds=child.interval_seconds), window=…, maintenance=no-op,
   computed_at=now)` — maintenance stays the documented no-op stopgap, but REWORD the stopgap
   comments so they no longer promise closed STORY-040 (say: real predicate arrives with the
   maintenance-wiring story).
4. `rollup = rollup_group(children_results, window=…, computed_at=now)`.
   Zero-signal component → `rollup_group([])` → 200 with `signals: []` and null percentages
   (degenerate propagates, never a 500 — same AC2 wording as the calculator's None handling).
DTOs in `availability/models.py`, frozen: `SignalAvailabilityDTO(AvailabilityDTO)` adding
`signal_key: str`; `ComponentAvailabilityDTO{component_id: str, rollup: AvailabilityDTO,
signals: list[SignalAvailabilityDTO]}`. New `validate_component_availability_request(
component_id, since, until)` in `validation.py`: non-empty id + the SAME parseable/tz-aware
checks (naive → 422, 2026-06-28 agreement; reuse/factor the existing datetime checks, don't
copy-paste them). Tests (fake-injected): multi-signal component with TWO DIFFERENT intervals
(e.g. 60 and 120 over the same window) proving each child's expected_cycles/completeness used
its own interval AND rollup = MIN of children percentages + SUM of counts; unknown component →
404; naive since → 422; no-data window → nulls not 500; zero-signal component → 200 empty
children; NULL-interval child → 409. Window tests must include a non-aligned (non-multiple)
window (2026-06-25 boundary agreement).

**D5 — AC3: the per-signal endpoint's interval default comes from the seeded topology.**
`controller.py`: `interval_seconds: int | None = Query(None, description="Cycle interval in
seconds; defaults to the signal's configured interval from the seeded topology")` —
`_DEFAULT_INTERVAL_SECONDS` and the "STORY-040 will supply" text are GONE from the controller.
`service.py::get_availability` resolution order:
- caller supplied a positive int → use it, NO topology lookup (back-compat pinned: an unknown
  signal_key with an explicit interval keeps today's degenerate all-None 200 behavior).
- caller supplied nothing → `signal_repo.get(signal_key)`: `None` → `SignalNotFoundError` →
  **404** (an unknown signal is now an honest 404 on the default path — the old behavior for
  this case is a CONTRACT CHANGE; rewrite any test that relied on it, never delete it);
  `interval_seconds is None` → `SignalIntervalUnconfiguredError` → **409**;
  else `interval = timedelta(seconds=sig.interval_seconds)`.
Controller catches the two new domain errors + `ComponentNotFoundError` (D4) and maps
404/409/404 respectively; `SyntacticValidationError` → 422 unchanged. Tests: default path uses
120 for a fake signal configured at 120 with observations at 120 s cadence → completeness is
~100 %, NOT ~50 % (the H2 regression proof — name it as such); explicit interval still wins;
unknown + default → 404; unknown + explicit → 200 degenerate; existing default-60 tests in
`test_availability_endpoint.py` REWRITTEN to the new contract (2026-06-29 agreement — the
`interval_seconds`-honored test survives rewritten, the fixture app now injects a
FakeSignalRepository).

**D6 — What explicitly does NOT change.** `core/services/availability.py` (calculator +
`rollup_group` consumed as-is), `core/services/pipeline.py`, `composition/orchestrate.py` +
`run.py`'s loop (they already take intervals from CONFIG via `SignalConfig.interval_seconds` —
the DB column is the API's read model, not the loop's), the maintenance no-op predicate
(comment reword only), `ApprovalService`/publisher chain, the frontend, existing endpoint
paths/DTOs other than stated.

## STORY-044 — topology + component availability + real intervals (5 pts) — AC1–AC4

- [x] **T1 — Migration + seed carry `interval_seconds` (D1), TDD.** Failing DB-gated test first
      (extend `test_seed.py`): after `seed_topology` with a config whose signal has
      `interval_seconds: 120`, the `signals` row carries 120; re-seed with 60 updates it
      (upsert `set_`). Then: new Alembic revision (chain from `eec78d2e8cbe`; module docstring
      names story + purpose like peers), extend `_SIGNALS` + values + `set_` in `seed.py`.
      `alembic upgrade head` + `downgrade` exercised by the existing migration tests/gate.
- [ ] **T2 — `Signal` domain type + `SignalRepository` port + adapter + fake (D2), TDD.**
      Failing parity contract test first: ONE test body against BOTH `FakeSignalRepository` and
      `PostgresSignalRepository` (DB-gated half via `migrated_db`, seeded through
      `seed_topology`): empty `[]`, signal_key ordering, `get` unknown → `None`, fields incl.
      NULL interval → `None`. Both-shapes validator tests for `Signal.interval_seconds > 0`.
      Then implement domain module (+ exports), port (+ exports), Postgres adapter, fake.
- [ ] **T3 — `api/v1/topology/` five-file module (D3, AC1), TDD.** Failing tests first: shape
      test (set equality, NAMED deliverable); fake-injected GET `/api/v1/topology` — empty →
      `[]`, multi-signal component nests sorted signals with all four fields, zero-signal
      component → `signals: []`, NULL-component_id signal appears nowhere. Then the module +
      `create_app`/`app.state`/`dependencies.py`/`api/v1/__init__.py` wiring. Finish with the
      DB-gated seeded end-to-end enumeration test (real Postgres repos + `seed_topology`,
      TestClient) proving "sourced from the seeded topology".
- [ ] **T4 — Component-rollup availability endpoint (D4, AC2), TDD.** Failing tests first (fake
      observation/component/signal repos through `create_app`): the two-interval multi-signal
      fixture proving per-child intervals + MIN/SUM rollup; 404 unknown component; 422 naive
      datetime; nulls on no-data; 200 empty-children on zero-signal component; 409 on
      NULL-interval child; non-aligned window included. Then: DTOs, validator, service method
      (+ ctor deps, shared window helper, call-site rewrites), controller route + error
      mapping.
- [ ] **T5 — Per-signal default interval from topology (D5, AC3), TDD.** Failing tests first:
      the H2 regression (default → 120 → completeness ~100 %), explicit-interval-wins, 404
      unknown-on-default-path, 200 degenerate unknown-with-explicit. Then controller param +
      service resolution + error mapping; REWRITE the existing default-interval tests.
- [ ] **T6 — Gates + docs + blast radius (AC4).** All six backend DoD commands exit 0 on a clean
      committed tree — SINGLE non-concurrent DB-gated run. CLAUDE.md: no command changes
      expected (command-sync N/A unless one changes). Wiki blast radius — your diff will touch
      `code_refs` of at least: `api-five-file-convention` (new module + availability changes),
      `canonical-types-and-ports` (new domain type + port), `persistence-adapters` (new
      adapter), `migrations-and-db` (new revision — ADD the new migration file to its
      `code_refs`), `config-layer` (only if `config.py`/yaml change — avoid),
      `core-pipeline-and-availability` (`test_availability.py` is in its code_refs — you should
      NOT need to touch that file; endpoint tests live in `test_availability_endpoint.py`).
      Update affected articles' Facts (symbol-cited, 2026-06-27) + bump `verified_sha`; REPORT
      which you touched; the orchestrator runs the mechanical sweep at the compile pass.

## Conventions checklist (held at quality review)
- Module + public-symbol docstrings citing the relevant dossier § (peers: `availability`
  feature files, `component_repository.py`, `seed.py` set the register).
- Frozen value/result types with cross-field invariants → `model_validator(mode="after")` +
  both-shapes tests (2026-06-26): applies to `Signal`.
- Empty-input AND non-aligned-boundary tests where applicable (2026-06-25): empty topology,
  zero-signal component, empty window, non-multiple window.
- Named domain errors, never bare `ValueError` (2026-06-28); map at the controller
  (404/409/422 as pinned).
- Fake/adapter parity for the new port — one contract test body, both impls (2026-06-26).
- A contract change REWRITES covering tests (AvailabilityService ctor, default-interval
  behavior, `create_app` signature) — never deletes them to a gap (2026-06-29).
- Composition/assembly tests construct REAL wired objects; mock only genuine I/O edges
  (2026-06-29).
- Five-file shape test for `topology/` (2026-06-28, set equality, mirror the named peers).
- Edge DTO maps `id=entity.id` directly — no sentinel fallback (2026-06-28).
- API datetime inputs tz-aware or 422 (2026-06-28) — applies to the new component endpoint.
- Scoped staging; commit-after-green; no `git add -A`; ruff-clean before each commit.
- Import boundaries: domain/ports import only core; adapter imports core (never another
  adapter); the api feature imports core ports + its own files (never another feature);
  `lint-imports` stays 5 kept / 0 broken.

## Guardrails (implementer)
- Build to THIS plan + `docs/scrum/stories/STORY-044-availability-topology-api.md` + dossier
  §7/§9/§11/§13/§17 — never chat history. D1–D6 are BINDING; genuine conflict between them and
  the code you find → STOP and report, don't improvise.
- Do NOT write `.scrum/` board state; do NOT run reviewers or merge — the orchestrator owns the
  back half. No live credentials needed anywhere (fakes + throwaway DB prove everything).
- Genuine ambiguity → STOP with the exact question. Effort > 3× the 5-pt estimate → STOP.
- Report: steps done + commit SHA each; every gate command + exit code + output tail; which wiki
  articles your diff touches (with what you updated); net-new/rewritten/deleted tests with the
  justification; anything noticed-but-not-done.

## Sequencing rationale
T1 first — the schema column is the foundation; without it nothing downstream is honest. T2 puts
the port + parity contract on top (the riskiest boundary, same slot as sprint 29's T1). T3 is the
first consumer (pure read, new module — no existing-contract ripple). T4 is the biggest surface
(new DTOs + service ctor change) while context on the port is fresh. T5 is the smallest diff but
carries the contract-change rewrite obligation, so it goes after the fixture plumbing T4 already
forces. T6 gates + wiki. Risk lives in the AvailabilityService ctor ripple through the existing
suite (D4 names the rewrite obligation) and in seed/migration coupling (D1 keeps the column
nullable so upgrade order can never strand a deploy).
