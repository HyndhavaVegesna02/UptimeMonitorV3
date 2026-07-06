---
title: Sample mode — the on-demand outage simulator (TEMPORARY feature)
code_refs: [migrations/versions/09e9aa2cee32_add_sample_mode.py, backend/src/core/ports/sample_mode_repository.py, backend/src/core/ports/__init__.py, backend/src/adapters/persistence/sample_mode_repository.py, backend/src/api/v1/sample_mode/__init__.py, backend/src/api/v1/sample_mode/controller.py, backend/src/api/v1/sample_mode/models.py, backend/src/api/v1/sample_mode/validation.py, backend/src/api/v1/sample_mode/service.py, backend/src/api/dependencies.py, backend/src/api/v1/__init__.py, backend/src/composition/app.py, backend/src/composition/sample_mode.py, backend/src/composition/run.py, pyproject.toml, backend/tests/fakes.py, backend/tests/test_sample_mode_repository_contract.py, backend/tests/test_sample_mode_endpoint.py, backend/tests/test_sample_mode_ingest.py, backend/tests/test_sample_mode_end_to_end.py, backend/tests/test_run_live_loop.py, frontend/src/api/types.ts, frontend/src/api/client.ts, frontend/src/mocks/handlers/sampleMode.ts, frontend/src/mocks/handlers/index.ts, frontend/src/features/dashboard/useSampleMode.ts, frontend/src/pages/DashboardPage.tsx, frontend/src/pages/DashboardPage.css]
verified_sha: e86493f
verified_sprint: sprint-33
status: verified          # verified | stale | archived
---

## PO directive (read first)
**This whole feature is TEMPORARY and will be DELETED.** (PO, 2026-07-03, at the
sprint-31 lock — STORY-048 AC7.) Every design decision below was chosen for
REMOVABILITY over integration: dedicated new files wherever possible, existing
files touched only at minimal seam points each marked with a
`# STORY-048 sample-mode seam (temporary — see docs/scrum/wiki/sample-mode.md)`
comment (grep for `STORY-048` to find every one), zero changes to canonical
domain types / existing tables / existing core services, and the flag OFF is
byte-identical to the system's behavior before this story. See **REMOVAL**
below for the mechanical deletion recipe.

## Facts (verified against code)

### What it does (dossier §6, §8, §17)
- The PO's problem: the real Dynatrace monitor is healthy, so the Approvals
  and Publications tabs are always empty and the approve→publish→recover loop
  can only be exercised with fakes. Sample mode is a global, persisted,
  process-crossing boolean flag: while ON, the live loop records EVERY
  incoming observation with `health=DOWN` (simulating an outage), so the REAL
  pipeline (streak → anti-flap → decide) opens a real degradation proposal
  that can be approved, published, and — after flipping the switch OFF —
  recovered from. Default OFF (PO answer, 2026-07-03).
- The two-process constraint (why this is DB-persisted, not an in-memory
  bool): the API server (`composition/app.py::create_app`) and the live loop
  (`composition/run.py::build_live_loop`) share ONLY the database — the flag
  must be readable from both processes.
- Hexagonal constraint: the forced-DOWN override is a COMPOSITION-layer
  concern, applied at the ingest edge — `core/domain/*` and `core/services/*`
  are untouched (STORY-048 Context).

### Storage — `sample_mode` table (D1)
- `migrations/versions/09e9aa2cee32_add_sample_mode.py` (`down_revision =
  "5ed254a8daab"`, chains from sprint-30's head) creates a dedicated,
  droppable, no-FK table: `sample_mode(id BOOLEAN PRIMARY KEY DEFAULT TRUE
  CHECK (id), enabled BOOLEAN NOT NULL, updated_at TIMESTAMPTZ NOT NULL
  DEFAULT now())`. The `CHECK (id)` constraint pins the table to AT MOST ONE
  row. `upgrade()` creates an EMPTY table — never-set → `False` is enforced
  by the PORT, not a seeded default row. Reversible (`downgrade()` drops the
  table); no FK in either direction, so `scripts/check_fk_direction.py`'s
  SPINE allowlist and violation count are unaffected.

### The port — `SampleModeRepository` (D2)
- `core/ports/sample_mode_repository.py::SampleModeRepository` (ABC): two
  methods. `is_enabled() -> bool` — `False` when the row was never set (the
  PO's default-OFF lives HERE), never raises. `set_enabled(enabled: bool) ->
  None` — idempotent upsert (`INSERT ... ON CONFLICT (id) DO UPDATE`);
  setting the current value again succeeds silently. No new domain type (the
  payload is a bare bool) and no domain error (there is no not-found case).
  Exported via `core/ports/__init__.py` (STORY-048 seam — one import line +
  one `__all__` entry, both comment-marked).
- `adapters/persistence/sample_mode_repository.py::PostgresSampleModeRepository`
  mirrors the peer adapters' style (injected `Engine`, lightweight `sa.table`,
  no ORM model). `is_enabled` is a plain `SELECT` on `sa.Engine.connect`
  (read-only); `set_enabled` is the upsert on `sa.Engine.begin`.
- `FakeSampleModeRepository` (`backend/tests/fakes.py`) accepts an optional
  `store: dict | None = None` constructor arg — the ONE fake in this codebase
  that supports a SHARED backing store across instances, needed to prove
  "persistence across a fresh repository instance" (mirroring what a fresh
  `PostgresSampleModeRepository(engine)` on the SAME engine proves for real)
  without adding DB infrastructure to a pure in-memory fake. Passing no
  `store` gives each instance its own private dict, matching every other
  fake's normal per-instance-only behavior.
- Fake/adapter parity (2026-06-26 agreement): ONE shared assertion body,
  `backend/tests/test_sample_mode_repository_contract.py::
  _assert_sample_mode_repository_contract(make_repo)`, run against both
  implementations (the Postgres half DB-gated via `migrated_db`) — proves
  never-set → `False`, set/read round-trips, idempotent re-set, and
  persistence across a fresh instance bound to the same store/engine.

### The API — `GET`/`PUT /api/v1/sample-mode` (D3)
- New five-file module `api/v1/sample_mode/` (dossier §13 convention):
  `__init__.py` (router re-export), `controller.py`
  (`sample_mode/controller.py::get_sample_mode` /
  `sample_mode/controller.py::set_sample_mode`), `models.py`
  (`sample_mode/models.py::SampleModeDTO` / `sample_mode/models.py::
  SampleModeUpdateRequest`, both frozen), `validation.py` (a documented no-op
  — the PUT body's only field is validated by Pydantic itself), `service.py`
  (`sample_mode/service.py::SampleModeService.get_state` /
  `sample_mode/service.py::SampleModeService.set_state` +
  `sample_mode/service.py::get_sample_mode_service` DI provider).
- `GET /sample-mode` → `SampleModeDTO{enabled: bool}` from `is_enabled()`.
  `PUT /sample-mode` with `{"enabled": true|false}` → applies `set_enabled`,
  returns the new `SampleModeDTO`; idempotent; a missing/non-boolean
  `enabled` field 422s via FastAPI/Pydantic's own body validation (no custom
  syntactic check needed).
- Wiring (mirrors sprint-30's `signal_repo` pattern exactly): `create_app`
  gained `sample_mode_repo: SampleModeRepository | None = None` (real branch
  builds `PostgresSampleModeRepository(engine)`), `app.state.sample_mode_repo`,
  `api/dependencies.py::get_sample_mode_repo`, router registered in
  `api/v1/__init__.py`, `src.api.v1.sample_mode` added to the
  `api-feature-independence` contract's `modules` list in `pyproject.toml`
  (lint-imports stays 5 kept / 0 broken — the contract's own module COUNT is
  unaffected; only that one contract's list grew, same shape as sprint-30's
  `topology` addition).
- Tests (`backend/tests/test_sample_mode_endpoint.py`): five-file shape
  assertion; fake-injected GET default false; PUT true→GET true, PUT
  false→GET false; idempotent re-PUT; missing-field and wrong-type body →
  422; ONE DB-gated round-trip through a real Postgres-backed `create_app`.

### The override — `SampleModeIngest` (D4, D5)
- `composition/sample_mode.py::SampleModeIngest(SignalIngestPort)` — a
  composition-layer decorator. Constructor `(delegate: SignalIngestPort,
  sample_mode_repo: SampleModeRepository)`. `ingest_observations(batch)`
  reads `sample_mode_repo.is_enabled()` EXACTLY ONCE per call — no caching,
  no TTL, no background refresh. Since each `run_periodic` cycle
  (`composition/pull_loop.py::run_periodic`) calls `ingest_observations`
  exactly once, this IS the per-cycle read AC4 requires: a flag flip between
  cycles changes the NEXT cycle's recording with no loop restart (proven by
  `backend/tests/test_sample_mode_ingest.py::
  test_flag_flip_between_cycles_affects_only_the_next_call`, a two-cycle
  fake-driven test).
- OFF → `return self._delegate.ingest_observations(batch)` with the SAME
  batch object instances passed through — no copy, no transform (AC7b
  byte-identical; asserted via `is` identity, not `==` equality).
- ON → each observation is replaced by
  `observation.model_copy(update={"health": Health.DOWN, "raw_ref":
  SIMULATED_RAW_REF})` — `signal_key`, `observed_at`, `source_event_id`,
  `source`, `location`, `latency_ms` all unchanged, so dedup and watermark
  behavior is identical regardless of the flag. A vendor-DOWN observation
  under ON stays DOWN + gets the marker too (no double-flip branching).
  Empty batch: `[]` transforms to `[]` — no special case, passes through
  under both states.
- A `sample_mode_repo.is_enabled()` read failure PROPAGATES — never
  swallowed — consistent with the loop's existing cycle-failure handling
  (the cycle already depends on the same database for everything else).
- `SIMULATED_RAW_REF = "sample-mode:forced-down"` (`composition/
  sample_mode.py::SIMULATED_RAW_REF`) is the AC5 marker (D5): a sentinel on
  the EXISTING `SignalObservation.raw_ref` field — ZERO schema/domain
  change. `raw_ref` is already persisted and round-tripped by
  `ObservationRepository`, is `None` on every genuine live HTTP row today,
  the core never reads it, and the history API deliberately omits it from
  its client DTO — so a simulated row is mechanically distinguishable
  (`raw_ref = 'sample-mode:forced-down'`, or SQL `WHERE raw_ref LIKE
  'sample-mode%'`) while NOTHING else in the system changes. The alternative
  (a new `simulated` column/field) would touch the canonical domain type +
  table + every constructor — exactly what the removability directive
  forbids.

### The seam — `composition/run.py::build_live_loop` (D4)
- The ONE existing-file production-code seam: step 2 of `build_live_loop`
  now wraps the real `IngestService` — `ingest_port = SampleModeIngest(
  delegate=IngestService(observation_repo=..., watermark_repo=...,
  rejected_repo=..., clock=...), sample_mode_repo=
  PostgresSampleModeRepository(engine))` — marked with the STORY-048 seam
  comment. The API process (`create_app`) never ingests anything, so its
  only sample-mode surface is the D3 endpoints — the decorator is NOT wired
  into any approval/publish path.
- `backend/tests/test_run_live_loop.py::test_build_live_loop_assembly` is
  the SANCTIONED AC7b exception (2026-06-29 assembly-test agreement +
  2026-06-29 contract-change-rewrites-tests agreement): its assertions were
  UPDATED to assert the REAL `SampleModeIngest` → `IngestService` nesting
  (constructed for real, only `run_periodic` mocked) rather than a bare
  `IngestService`. The pre-existing BEHAVIOR tests —
  `backend/tests/test_pull_loop.py` and `backend/tests/test_ingest_service.py`
  — were NOT touched and pass unmodified; neither file appears in this
  article's `code_refs` because neither changed.

### Operational gotchas (live-verified 2026-07-06 debug sprint)
- **The flip is NOT retroactive.** Forced copies keep `source_event_id` unchanged (D4
  above: "dedup and watermark behavior is identical regardless of the flag"), so any
  observation already persisted as `up` before the flip stays `up` forever — DOWN applies
  only to events ingested in cycles AFTER the flip. The first-ever cycle backfills
  Grail's ~2h default scan window; flipping ON after that leaves Check History
  overwhelmingly "up" while new events trickle in DOWN one per minute. For an all-down
  demo, flip ON before starting the loop against a fresh DB.
- **The flag row lives per DB instance.** Recreating the throwaway dev Postgres
  (`scripts/dev_db.py up`, or the pytest `migrated_db` fixture) resets `sample_mode` to
  empty = OFF. The Dashboard toggle meanwhile keeps showing ON from
  `useSampleMode`'s client-side override (it reflects the last successful PUT and never
  re-polls) — the UI can show ON against a database whose flag is OFF. Diagnostic order
  when "sample mode is on but rows are up": `select * from sample_mode` in the DB the
  LOOP reads → watermark advancing across two cycles → `select health, raw_ref,
  max(observed_at) from observations group by 1,2`. Full evidence trail:
  `docs/scrum/sprints/2026-07-06-debug-sample-mode/report.md`.

### The frontend consumer — Dashboard sample-mode toggle (STORY-049)
- The Dashboard tab (`frontend/src/pages/DashboardPage.tsx`) renders a real
  `<button role="switch">` reflecting `GET /api/v1/sample-mode` on load and
  PUTting on click; `features/dashboard/useSampleMode.ts` owns both the load
  and the mutation (see `docs/scrum/wiki/frontend-zone.md`'s per-tab-pattern
  section for the design rationale — one hook, not the Approvals split,
  because there is no list to reconcile against). While ON, a tokens-styled
  "sample mode — signals recorded as DOWN" warning is shown. This is the
  ONLY frontend surface sample mode has; no other tab/page renders anything
  related to it.

### End-to-end proof (T5)
- `backend/tests/test_sample_mode_end_to_end.py` drives observations through
  the REAL `IngestService` (in-memory fake repos, no DB) wrapped by
  `SampleModeIngest`: flag ON → rows actually PERSISTED by the real ingest
  chain are `health=DOWN` + `raw_ref=SIMULATED_RAW_REF`; flag OFF → persisted
  rows are the SAME instances as the vendor payload (byte-identical). This is
  the story's reason-to-exist regression.

## REMOVAL (STORY-048 AC7c — the mechanical deletion recipe)

When sample mode is removed, the following is the COMPLETE, mechanical
checklist — nothing else in the system depends on any of it:

**Delete these files entirely:**
- `backend/src/composition/sample_mode.py`
- `backend/src/api/v1/sample_mode/` (all five files)
- `backend/src/core/ports/sample_mode_repository.py`
- `backend/src/adapters/persistence/sample_mode_repository.py`
- `backend/tests/test_sample_mode_repository_contract.py`
- `backend/tests/test_sample_mode_endpoint.py`
- `backend/tests/test_sample_mode_ingest.py`
- `backend/tests/test_sample_mode_end_to_end.py`
- `frontend/src/features/dashboard/useSampleMode.ts` (STORY-049 — the
  load+mutate hook)
- `frontend/src/features/dashboard/useSampleMode.test.tsx`
- `frontend/src/mocks/handlers/sampleMode.ts` (STORY-049 — the MSW GET/PUT
  handlers + fixture)
- This article, `docs/scrum/wiki/sample-mode.md` (archive/delete it too).

**Revert these marked seam lines** (grep the tree for `STORY-048` — every
touch point carries the comment `# STORY-048 sample-mode seam (temporary —
see docs/scrum/wiki/sample-mode.md)` immediately above or beside it):
- `backend/src/core/ports/__init__.py` — remove the `SampleModeRepository`
  import line + its `__all__` entry.
- `backend/tests/fakes.py` — remove the `SampleModeRepository` import line +
  the `FakeSampleModeRepository` class.
- `backend/src/composition/app.py` — remove the `sample_mode_repo` param,
  its `PostgresSampleModeRepository` import + wiring, the `app.state.
  sample_mode_repo` assignment.
- `backend/src/api/dependencies.py` — remove the `SampleModeRepository`
  import + `get_sample_mode_repo`.
- `backend/src/api/v1/__init__.py` — remove the `sample_mode` router import
  + `include_router` call.
- `backend/src/composition/run.py` — restore step 2 to a bare
  `ingest_port = IngestService(observation_repo=..., watermark_repo=...,
  rejected_repo=..., clock=...)` (undo the `SampleModeIngest` wrap + its two
  import lines).
- `pyproject.toml` — remove `"src.api.v1.sample_mode"` from the
  `api-feature-independence` contract's `modules` list.
- `backend/tests/test_run_live_loop.py` — revert
  `test_build_live_loop_assembly`'s `ingest_port` assertions back to a bare
  `IngestService` check (undo the `SampleModeIngest`/`IngestService` extra
  imports too).

**Revert these frontend shared-file edits** (STORY-049 — no comment tag was
added in the frontend code the way the backend uses `# STORY-048 sample-mode
seam`; instead every touched export/section carries a doc-comment naming
"TEMPORARY FEATURE" and pointing at this article — grep the tree for
`sample-mode.md` under `frontend/src` to find every one):
- `frontend/src/api/types.ts` — remove the `SampleModeDTO` interface.
- `frontend/src/api/client.ts` — remove `getSampleMode`/`putSampleMode` and
  the `putJson` helper (added by this story specifically to support the PUT;
  check no other endpoint has since adopted it before deleting it).
- `frontend/src/api/client.test.ts` — remove the `getSampleMode` import +
  the `getSampleMode`/`putSampleMode` `describe` blocks.
- `frontend/src/mocks/handlers/index.ts` — remove the `sampleMode` import
  line, its spread into `handlers`, and the `FIXTURE_SAMPLE_MODE_OFF`
  re-export.
- `frontend/src/pages/DashboardPage.tsx` — remove the `useSampleMode` import,
  the `SampleModeToggle` component, and its `<SampleModeToggle />` render
  call inside `DashboardPage`.
- `frontend/src/pages/DashboardPage.css` — remove the
  `.dashboard-sample-mode*` rule block (delimited by the "Sample-mode toggle
  (STORY-049)" comment).
- `frontend/src/pages/DashboardPage.test.tsx` — remove the "DashboardPage —
  sample mode toggle (STORY-049)" `describe` block; revert the `waitFor`
  import back to `{ render, screen, within }` if nothing else in the file
  still needs it.

**Write a new migration** chaining from whatever is HEAD at removal time
that DROPs the `sample_mode` table (`op.drop_table("sample_mode")`) — the
existing `09e9aa2cee32_add_sample_mode.py` migration itself is NOT deleted
(migrations are an append-only, immutable history; the new DROP migration is
the removal, mirroring how this table's own creation is one forward
migration).

**Data cleanup:** any simulated rows already written to a real `observations`
table are identifiable by the D5 sentinel — `WHERE raw_ref LIKE
'sample-mode%'` — for manual cleanup/deletion if desired; removing the code
does not retroactively touch already-persisted rows.

**What is untouched by removal** (D7 — never had a seam in the first place):
`core/domain/*`, `core/services/*`, `composition/pull_loop.py`,
`composition/seed.py`, all pre-existing tables/migrations, all pre-existing
backend endpoints, and — on the frontend side (STORY-049) — every OTHER
tab/feature (`useComponents`, `useApprovals`, `useAvailability`,
`AvailabilityPage`, `ApprovalsPage`), `lib/useFetch.ts` itself (unchanged),
and `mocks/handlers/{components,approvals,availability}.ts`. The
publisher/approval chain needs no change either way — sample mode only ever
produced ordinary data flowing through it.

## History
- sprint-34 (STORY-015f, unrelated story — mechanical staleness sweep only): the same three
  `code_refs` (`frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
  `frontend/src/mocks/handlers/index.ts`) changed again, but ONLY additively — STORY-015f (the
  Maintenance tab) added its own `MaintenanceWindowDTO`/`CreateMaintenanceRequest`,
  `getMaintenance`/`postMaintenance`, and `maintenanceHandlers` import/spread alongside the
  existing sample-mode content in those same shared files. `client.ts` also gained an optional
  `ApiError.detail` field (populated from any non-2xx `{"detail": ...}` body, not just
  sample-mode's) — purely additive to the `ApiError` shape, does not touch `getSampleMode`/
  `putSampleMode`/`putJson` themselves. Re-checked the REMOVAL recipe above line-by-line: it still
  names exact sample-mode-only lines/blocks in each file, none of which moved or were touched by
  STORY-015f; `putJson` is still adopted by no other endpoint (STORY-015f's `postMaintenance` uses
  `postJson`), so that removal caveat remains accurate too. No Facts changed. verified_sha =
  e86493f.
- 2026-07-06 (debug sprint, no story — `docs/scrum/sprints/2026-07-06-debug-sample-mode/
  report.md`): added the "Operational gotchas" section after a PO report ("sample mode ON
  but Check History shows up") was root-caused as environmental, not a code defect. The
  full chain (PUT → flag row → per-cycle read → forced-DOWN ingest → history API) was
  live-verified BOTH ways against real Grail on branch
  `debug/sample-mode-forced-down-not-applied`: flag ON → 120/120 + 2/2 rows `down` with
  the D5 sentinel across two advancing-watermark cycles; flag OFF → subsequent rows
  genuine `up`, `raw_ref` NULL. No Facts changed — the gotchas make explicit what D4's
  dedup-unchanged fact already implied operationally. verified_sha = 1257cc9.
- sprint-33 (STORY-015g, unrelated story — mechanical staleness sweep only): the same three
  `code_refs` (`frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
  `frontend/src/mocks/handlers/index.ts`) changed again, but ONLY additively — STORY-015g (the
  Publications tab) added its own `PublicationDTO`, `getPublications`, and `publicationsHandlers`
  import/spread alongside the existing sample-mode content in those same shared files, none of
  which moved or were touched. Re-checked the REMOVAL recipe above line-by-line: it still names
  exact sample-mode-only lines/blocks in each file; still accurate as written. No Facts changed.
  verified_sha = b7811cf.
- sprint-33 (STORY-015e, unrelated story — mechanical staleness sweep only): three of this
  article's `code_refs` (`frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
  `frontend/src/mocks/handlers/index.ts`) changed, but ONLY additively — STORY-015e (the Check
  History tab) added its own `ObservationDTO`, `getHistory`, and `historyHandlers` import/spread
  alongside the existing sample-mode content in those same shared files. Re-checked the REMOVAL
  recipe above line-by-line: it still names exact sample-mode-only lines/blocks in each file, none
  of which moved or were touched by STORY-015e, so the recipe remains accurate as written. No Facts
  changed. verified_sha = 0a1ef52.
- sprint-32 (STORY-049): updated. Landed the frontend consumer — the
  Dashboard sample-mode toggle (see the new "The frontend consumer" section
  above) — and extended the REMOVAL inventory with every frontend
  file/seam it added (`useSampleMode.ts`/`.test.tsx`, `mocks/handlers/
  sampleMode.ts`, and the shared-file edits to `api/types.ts`, `api/
  client.ts` (+ the new `putJson` helper), `api/client.test.ts`,
  `mocks/handlers/index.ts`, `pages/DashboardPage.{tsx,css,test.tsx}`).
  Corrected the D7 "untouched by removal" list, which previously (wrongly,
  as of this story) named "the frontend" wholesale. `code_refs` +=
  the seven frontend files above. Frontend-only change; six backend gates
  untouched-green (empty diff — no backend source change), three frontend
  gates green. verified_sha = 63886bc.
- sprint-31 (STORY-048): created. PO directive at lock, 2026-07-03: a
  TEMPORARY feature; removability is a first-class AC (AC7). D1–D7 pinned in
  `docs/scrum/sprints/2026-07-03-sprint-31/plan.md`. verified_sha → 0ea652e
  (the last code commit before this article; T1–T5 landed as five separate
  TDD commits, each touching only dedicated new files plus the marked seam
  points named above).
