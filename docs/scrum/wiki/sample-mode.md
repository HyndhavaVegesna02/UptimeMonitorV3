---
title: Sample mode â€” the on-demand outage simulator (TEMPORARY feature)
code_refs: [backend/src/core/ports/sample_mode_repository.py, backend/src/core/ports/__init__.py, backend/src/api/v1/sample_mode/__init__.py, backend/src/api/v1/sample_mode/controller.py, backend/src/api/v1/sample_mode/models.py, backend/src/api/v1/sample_mode/validation.py, backend/src/api/v1/sample_mode/service.py, backend/src/api/dependencies.py, backend/src/api/v1/__init__.py, backend/src/composition/app.py, backend/src/composition/sample_mode.py, backend/src/composition/run.py, pyproject.toml, backend/tests/fakes.py, backend/tests/test_sample_mode_repository_contract.py, backend/tests/test_sample_mode_endpoint.py, backend/tests/test_sample_mode_ingest.py, backend/tests/test_sample_mode_end_to_end.py, backend/tests/test_run_live_loop.py, frontend/src/api/types.ts, frontend/src/api/client.ts, frontend/src/mocks/handlers/sampleMode.ts, frontend/src/mocks/handlers/index.ts, frontend/src/features/dashboard/useSampleMode.ts, frontend/src/AppShell.tsx, frontend/src/nav/SampleModeSwitch.tsx, frontend/src/nav/SampleModeChip.tsx, frontend/src/nav/SampleModeBanner.tsx, frontend/src/nav/useDismissibleBanner.ts, backend/tests/test_ingest_service.py, backend/tests/test_pull_loop.py, backend/src/adapters/persistence/dynamo_sample_mode_repository.py]
verified_sha: 5dd72ce
verified_sprint: sprint-55
status: verified
---

## PO directive (read first)
**This whole feature is TEMPORARY and will be DELETED.** (PO, 2026-07-03, at the
sprint-31 lock â€” STORY-048 AC7.) Every design decision below was chosen for
REMOVABILITY over integration: dedicated new files wherever possible, existing
files touched only at minimal seam points each marked with a
`# STORY-048 sample-mode seam (temporary â€” see docs/scrum/wiki/sample-mode.md)`
comment (grep for `STORY-048` to find every one), zero changes to canonical
domain types / existing tables / existing core services, and the flag OFF is
byte-identical to the system's behavior before this story. See **REMOVAL**
below for the mechanical deletion recipe.

## Facts (verified against code)

### What it does (dossier Â§6, Â§8, Â§17)
- The PO's problem: the real Dynatrace monitor is healthy, so the Approvals
  and Publications tabs are always empty and the approveâ†’publishâ†’recover loop
  can only be exercised with fakes. Sample mode is a global, persisted,
  process-crossing boolean flag: while ON, the live loop records EVERY
  incoming observation with `health=DOWN` (simulating an outage), so the REAL
  pipeline (streak â†’ anti-flap â†’ decide) opens a real degradation proposal
  that can be approved, published, and â€” after flipping the switch OFF â€”
  recovered from. Default OFF (PO answer, 2026-07-03).
- The two-process constraint (why this is DB-persisted, not an in-memory
  bool): the API server (`composition/app.py::create_app`) and the live loop
  (`composition/run.py::build_live_loop`) share ONLY the database â€” the flag
  must be readable from both processes.
- Hexagonal constraint: the forced-DOWN override is a COMPOSITION-layer
  concern, applied at the ingest edge â€” `core/domain/*` and `core/services/*`
  are untouched (STORY-048 Context).

### Storage â€” DynamoDB Sample Mode (D1)
- The sample mode status is stored in the control table under partition key `SAMPLE_MODE` and sort key `META` (via `DynamoSampleModeRepository`). There are no foreign keys or relational constraints, keeping it isolated. Default value `False` is enforced by the PORT when no item exists.


### The port â€” `SampleModeRepository` (D2)
- `core/ports/sample_mode_repository.py::SampleModeRepository` (ABC): two
  methods. `is_enabled() -> bool` â€” `False` when the row was never set (the
  PO's default-OFF lives HERE), never raises. `set_enabled(enabled: bool) ->
  None` â€” idempotent upsert (`INSERT ... ON CONFLICT (id) DO UPDATE`);
  setting the current value again succeeds silently. No new domain type (the
  payload is a bare bool) and no domain error (there is no not-found case).
  Exported via `core/ports/__init__.py` (STORY-048 seam â€” one import line +
  one `__all__` entry, both comment-marked).
- `adapters/persistence/sample_mode_repository.py::PostgresSampleModeRepository`
  mirrors the peer adapters' style (injected `Engine`, lightweight `sa.table`,
  no ORM model). `is_enabled` is a plain `SELECT` on `sa.Engine.connect`
  (read-only); `set_enabled` is the upsert on `sa.Engine.begin`.
- `FakeSampleModeRepository` (`backend/tests/fakes.py`) accepts an optional
  `store: dict[str, bool] | None = None` constructor arg (parametrized
  STORY-047 AC5, matching the peer fakes' style â€” the store actually holds
  `{"enabled": bool}`) â€” the ONE fake in this codebase
  that supports a SHARED backing store across instances, needed to prove
  "persistence across a fresh repository instance" (mirroring what a fresh
  `PostgresSampleModeRepository(engine)` on the SAME engine proves for real)
  without adding DB infrastructure to a pure in-memory fake. Passing no
  `store` gives each instance its own private dict, matching every other
  fake's normal per-instance-only behavior.
- Fake/adapter parity (2026-06-26 agreement): ONE shared assertion body,
  `backend/tests/test_sample_mode_repository_contract.py::
  _assert_sample_mode_repository_contract(make_repo)`, run against both
  implementations (the Postgres half DB-gated via `migrated_db`) â€” proves
  never-set â†’ `False`, set/read round-trips, idempotent re-set, and
  persistence across a fresh instance bound to the same store/engine.

### The API â€” `GET`/`PUT /api/v1/sample-mode` (D3)
- New five-file module `api/v1/sample_mode/` (dossier Â§13 convention):
  `__init__.py` (router re-export), `controller.py`
  (`sample_mode/controller.py::get_sample_mode` /
  `sample_mode/controller.py::set_sample_mode`), `models.py`
  (`sample_mode/models.py::SampleModeDTO` / `sample_mode/models.py::
  SampleModeUpdateRequest`, both frozen), `validation.py` (a documented no-op
  â€” the PUT body's only field is validated by Pydantic itself), `service.py`
  (`sample_mode/service.py::SampleModeService.get_state` /
  `sample_mode/service.py::SampleModeService.set_state` +
  `sample_mode/service.py::get_sample_mode_service` DI provider).
- `GET /sample-mode` â†’ `SampleModeDTO{enabled: bool}` from `is_enabled()`.
  `PUT /sample-mode` with `{"enabled": true|false}` â†’ applies `set_enabled`,
  returns the new `SampleModeDTO`; idempotent; a missing/non-boolean
  `enabled` field 422s via FastAPI/Pydantic's own body validation (no custom
  syntactic check needed).
- Wiring (mirrors sprint-30's `signal_repo` pattern exactly): `create_app`
  gained `sample_mode_repo: SampleModeRepository | None = None` (real branch
  builds `PostgresSampleModeRepository(engine)`), `app.state.sample_mode_repo`,
  `api/dependencies.py::get_sample_mode_repo`, router registered in
  `api/v1/__init__.py`, `src.api.v1.sample_mode` added to the
  `api-feature-independence` contract's `modules` list in `pyproject.toml`
  (lint-imports stays 5 kept / 0 broken â€” the contract's own module COUNT is
  unaffected; only that one contract's list grew, same shape as sprint-30's
  `topology` addition).
- Tests (`backend/tests/test_sample_mode_endpoint.py`): five-file shape
  assertion; fake-injected GET default false; PUT trueâ†’GET true, PUT
  falseâ†’GET false; idempotent re-PUT; missing-field and wrong-type body â†’
  422; ONE DB-gated round-trip through a real Postgres-backed `create_app`.

### The override â€” `SampleModeIngest` (D4, D5)
- `composition/sample_mode.py::SampleModeIngest(SignalIngestPort)` â€” a
  composition-layer decorator. Constructor `(delegate: SignalIngestPort,
  sample_mode_repo: SampleModeRepository)`. `ingest_observations(batch)`
  reads `sample_mode_repo.is_enabled()` EXACTLY ONCE per call â€” no caching,
  no TTL, no background refresh. Since each `run_periodic` cycle
  (`composition/pull_loop.py::run_periodic`) calls `ingest_observations`
  exactly once, this IS the per-cycle read AC4 requires: a flag flip between
  cycles changes the NEXT cycle's recording with no loop restart (proven by
  `backend/tests/test_sample_mode_ingest.py::
  test_flag_flip_between_cycles_affects_only_the_next_call`, a two-cycle
  fake-driven test).
- OFF â†’ `return self._delegate.ingest_observations(batch)` with the SAME
  batch object instances passed through â€” no copy, no transform (AC7b
  byte-identical; asserted via `is` identity, not `==` equality).
- ON â†’ each observation is replaced by
  `observation.model_copy(update={"health": Health.DOWN, "raw_ref":
  SIMULATED_RAW_REF})` â€” `signal_key`, `observed_at`, `source_event_id`,
  `source`, `location`, `latency_ms` all unchanged, so dedup and watermark
  behavior is identical regardless of the flag. A vendor-DOWN observation
  under ON stays DOWN + gets the marker too (no double-flip branching).
  Empty batch: `[]` transforms to `[]` â€” no special case, passes through
  under both states.
- A `sample_mode_repo.is_enabled()` read failure PROPAGATES â€” never
  swallowed â€” consistent with the loop's existing cycle-failure handling
  (the cycle already depends on the same database for everything else).
- `SIMULATED_RAW_REF = "sample-mode:forced-down"` (`composition/
  sample_mode.py::SIMULATED_RAW_REF`) is the AC5 marker (D5): a sentinel on
  the EXISTING `SignalObservation.raw_ref` field â€” ZERO schema/domain
  change. `raw_ref` is already persisted and round-tripped by
  `ObservationRepository`, is `None` on every genuine live HTTP row today,
  the core never reads it, and the history API deliberately omits it from
  its client DTO â€” so a simulated row is mechanically distinguishable
  (`raw_ref = 'sample-mode:forced-down'`, or SQL `WHERE raw_ref LIKE
  'sample-mode%'`) while NOTHING else in the system changes. The alternative
  (a new `simulated` column/field) would touch the canonical domain type +
  table + every constructor â€” exactly what the removability directive
  forbids.

### The seam â€” `composition/run.py::build_live_loop` (D4)
- The ONE existing-file production-code seam: step 2 of `build_live_loop`
  now wraps the real `IngestService` â€” `ingest_port = SampleModeIngest(
  delegate=IngestService(observation_repo=..., watermark_repo=...,
  rejected_repo=..., clock=...), sample_mode_repo=
  PostgresSampleModeRepository(engine))` â€” marked with the STORY-048 seam
  comment. The API process (`create_app`) never ingests anything, so its
  only sample-mode surface is the D3 endpoints â€” the decorator is NOT wired
  into any approval/publish path.
- `backend/tests/test_run_live_loop.py::test_build_live_loop_assembly` is
  the SANCTIONED AC7b exception (2026-06-29 assembly-test agreement +
  2026-06-29 contract-change-rewrites-tests agreement): its assertions were
  UPDATED to assert the REAL `SampleModeIngest` â†’ `IngestService` nesting
  (constructed for real, only `run_periodic` mocked) rather than a bare
  `IngestService`. The pre-existing BEHAVIOR tests â€”
  `backend/tests/test_pull_loop.py` and `backend/tests/test_ingest_service.py`
  â€” were NOT touched and pass unmodified.

### Operational gotchas (live-verified 2026-07-06 debug sprint)
- **The flip is NOT retroactive.** Forced copies keep `source_event_id` unchanged (D4
  above: "dedup and watermark behavior is identical regardless of the flag"), so any
  observation already persisted as `up` before the flip stays `up` forever â€” DOWN applies
  only to events ingested in cycles AFTER the flip. The first-ever cycle backfills
  Grail's ~2h default scan window; flipping ON after that leaves Check History
  overwhelmingly "up" while new events trickle in DOWN one per minute. For an all-down
  demo, flip ON before starting the loop against a fresh DB.
- **The flag row lives per DB instance.** Recreating the throwaway dev Postgres
  (`scripts/dev_db.py up`, or the pytest `migrated_db` fixture) resets `sample_mode` to
  empty = OFF. The Dashboard toggle meanwhile keeps showing ON from
  `useSampleMode`'s client-side override (it reflects the last successful PUT and never
  re-polls) â€” the UI can show ON against a database whose flag is OFF. Diagnostic order
  when "sample mode is on but rows are up": `select * from sample_mode` in the DB the
  LOOP reads â†’ watermark advancing across two cycles â†’ `select health, raw_ref,
  max(observed_at) from observations group by 1,2`. Full evidence trail:
  `docs/scrum/sprints/2026-07-06-debug-sample-mode/report.md`.

### The frontend consumer â€” shell TopBar trigger + banner (STORY-049, relocated STORY-056)
- **STORY-056 (sprint-38) relocated this OUT of `DashboardPage` and into the app shell** â€” every
  tab renders inside the shell, so the trigger no longer needs to live on one specific tab. The
  hook itself, `features/dashboard/useSampleMode.ts`, is UNCHANGED (still owns both the load
  `useFetch(getSampleMode)` and the mutation `setEnabled`; see
  `docs/scrum/wiki/frontend-zone.md`'s per-tab-pattern section for the one-hook design rationale).
  What changed is WHO calls it and WHERE it renders:
  - `frontend/src/AppShell.tsx` calls `useSampleMode()` exactly ONCE and passes the result down as
    a prop to both consumers below â€” never two independent hook calls, which would each run their
    own GET/override cycle and could disagree the instant one of them PUTs.
  - `frontend/src/nav/TopBar.tsx` renders the real `<button role="switch" aria-checked
    aria-label="Sample mode">` (now a âš¡ icon button, right-aligned in the top bar) â€” same
    role/state contract as the old inline toggle; a GET failure now renders a small retry
    affordance in the trigger's place instead of a load failure falling back to the full shell
    `ErrorState` (a 32px icon slot has no room for that block); a failed PUT surfaces a visible
    `role="alert"` next to the buttons.
  - `frontend/src/nav/SampleModeBanner.tsx` renders the exact "sample mode â€” signals recorded as
    DOWN" `role="status"` warning text from the old inline block, now in a shell-level banner
    region under the top bar, and now DISMISSIBLE (session-scoped local state; re-arms whenever the
    flag transitions off then on again).
  - `frontend/src/pages/DashboardPage.tsx` no longer imports `useSampleMode` or renders anything
    sample-mode-related â€” it is a plain read tab again, same shape as Availability/Publications.
  This is still the ONLY frontend surface sample mode has; no other tab/page renders anything
  related to it â€” the surface just moved from "inside one tab's page" to "the shell every tab
  renders inside."

### CURRENT STATE on `sprint-55`/`ui-rewrite` - STORY-104 restored the frontend surface on the new shell (re-verified, NOT just a trivial re-check)
- STORY-103 (the PO-ordered full UI rewrite, "Mission Teal") had deleted `nav/TopBar.tsx`,
  the old `nav/SampleModeBanner.tsx`, and `pages/DashboardPage.tsx` outright and shipped a
  minimal top-bar-stub `AppShell.tsx` with no sample-mode surface at all - see the History
  entry below for that interim state. **STORY-104 (this sprint's follow-on story) restored the
  surface on the new Mission Teal shell** - the frontend sample-mode switch/banner/chip trio
  described in "The frontend consumer" section above is once again live in the routed app, on
  new components at NEW paths:
  - `frontend/src/nav/SampleModeSwitch.tsx` (NEW file, same path segment `nav/` but a new name -
    not a re-creation of the deleted `TopBar.tsx`) - the `role="switch"`/`aria-checked` trigger,
    ported verbatim in BEHAVIOR from the deleted `TopBar`'s embedded switch block (same
    `useSampleMode()` prop contract, same neutral-OFF/degraded-amber-ON rule, same visible-label-
    at->=768px rule), re-skinned onto Mission Teal tokens.
  - `frontend/src/nav/SampleModeChip.tsx` (NEW file) - the persistent "SAMPLE" chip, ported
    verbatim in BEHAVIOR from the deleted `TopBar`'s embedded chip button.
  - `frontend/src/nav/SampleModeBanner.tsx` (NEW file at the SAME path the STORY-103-deleted one
    used to occupy) - the dismissible `role="status"` warning, ported verbatim (same props, same
    text, same CSS class names) from the STORY-102 version `git show ui-redesign:frontend/src/
    nav/SampleModeBanner.tsx` describes.
  - `frontend/src/nav/useDismissibleBanner.ts` (NEW file, ported verbatim from `ui-redesign`
    STORY-102 - salvage list) - lifts the banner's dismiss/re-arm state so the chip and the
    banner can never disagree.
  - `frontend/src/AppShell.tsx` calls `useSampleMode()` exactly ONCE again (restoring the
    STORY-049/056 single-source-of-truth rule) and threads the result to `nav/CommandBar.tsx`
    (which renders the switch + the chip inline in its right cluster) and to the restored
    `SampleModeBanner` (rendered directly by `AppShell`, below the command bar).
  This is a full functional restoration, not merely a re-skin: `AppShell.test.tsx`'s sample-mode
  describe blocks re-prove the exact same behaviors the pre-rewrite `AppShell.test.tsx` did (switch
  reflects GET state, PUT updates it with no optimistic flip, banner shows only when
  ON-and-not-dismissed, the persistent chip appears once dismissed and survives a tab switch,
  clicking the chip restores the banner).
- **What is STILL unchanged throughout the whole rewrite (STORY-103 AND STORY-104):**
  `features/dashboard/useSampleMode.ts` and its test (`useSampleMode.test.tsx`) - the load+mutate
  hook itself, byte-identical to the STORY-049/056 shape described above, still exercising the same
  `getSampleMode`/`putSampleMode` client fns and the same MSW `mocks/handlers/sampleMode.ts`.
  Nothing on the backend, in `api/types.ts`/`api/client.ts`, or in the mock handlers changed by
  either rewrite story.

### End-to-end proof (T5)
- `backend/tests/test_sample_mode_end_to_end.py` drives observations through
  the REAL `IngestService` (in-memory fake repos, no DB) wrapped by
  `SampleModeIngest`: flag ON â†’ rows actually PERSISTED by the real ingest
  chain are `health=DOWN` + `raw_ref=SIMULATED_RAW_REF`; flag OFF â†’ persisted
  rows are the SAME instances as the vendor payload (byte-identical). This is
  the story's reason-to-exist regression.

## REMOVAL (STORY-048 AC7c â€” the mechanical deletion recipe)

When sample mode is removed, the following is the COMPLETE, mechanical
checklist â€” nothing else in the system depends on any of it:

**Delete these files entirely:**
- `backend/src/composition/sample_mode.py`
- `backend/src/api/v1/sample_mode/` (all five files)
- `backend/src/core/ports/sample_mode_repository.py`
- `backend/src/adapters/persistence/sample_mode_repository.py`
- `backend/tests/test_sample_mode_repository_contract.py`
- `backend/tests/test_sample_mode_endpoint.py`
- `backend/tests/test_sample_mode_ingest.py`
- `backend/tests/test_sample_mode_end_to_end.py`
- `frontend/src/features/dashboard/useSampleMode.ts` (STORY-049 â€” the
  load+mutate hook)
- `frontend/src/features/dashboard/useSampleMode.test.tsx`
- `frontend/src/mocks/handlers/sampleMode.ts` (STORY-049 â€” the MSW GET/PUT
  handlers + fixture)
- This article, `docs/scrum/wiki/sample-mode.md` (archive/delete it too).

**Revert these marked seam lines** (grep the tree for `STORY-048` â€” every
touch point carries the comment `# STORY-048 sample-mode seam (temporary â€”
see docs/scrum/wiki/sample-mode.md)` immediately above or beside it):
- `backend/src/core/ports/__init__.py` â€” remove the `SampleModeRepository`
  import line + its `__all__` entry.
- `backend/tests/fakes.py` â€” remove the `SampleModeRepository` import line +
  the `FakeSampleModeRepository` class.
- `backend/src/composition/app.py` â€” remove the `sample_mode_repo` param,
  its `PostgresSampleModeRepository` import + wiring, the `app.state.
  sample_mode_repo` assignment.
- `backend/src/api/dependencies.py` â€” remove the `SampleModeRepository`
  import + `get_sample_mode_repo`.
- `backend/src/api/v1/__init__.py` â€” remove the `sample_mode` router import
  + `include_router` call.
- `backend/src/composition/run.py` â€” restore step 2 to a bare
  `ingest_port = IngestService(observation_repo=..., watermark_repo=...,
  rejected_repo=..., clock=...)` (undo the `SampleModeIngest` wrap + its two
  import lines).
- `pyproject.toml` â€” remove `"src.api.v1.sample_mode"` from the
  `api-feature-independence` contract's `modules` list.
- `backend/tests/test_run_live_loop.py` â€” revert
  `test_build_live_loop_assembly`'s `ingest_port` assertions back to a bare
  `IngestService` check (undo the `SampleModeIngest`/`IngestService` extra
  imports too).

**Revert these frontend shared-file edits** (STORY-049, relocated STORY-056 â€” no comment tag was
added in the frontend code the way the backend uses `# STORY-048 sample-mode
seam`; instead every touched export/section carries a doc-comment naming
"TEMPORARY FEATURE" and pointing at this article â€” grep the tree for
`sample-mode.md` under `frontend/src` to find every one):
- `frontend/src/api/types.ts` â€” remove the `SampleModeDTO` interface.
- `frontend/src/api/client.ts` â€” remove `getSampleMode`/`putSampleMode` and
  the `putJson` helper (added by this story specifically to support the PUT;
  check no other endpoint has since adopted it before deleting it).
- `frontend/src/api/client.test.ts` â€” remove the `getSampleMode` import +
  the `getSampleMode`/`putSampleMode` `describe` blocks.
- `frontend/src/mocks/handlers/index.ts` â€” remove the `sampleMode` import
  line, its spread into `handlers`, and the `FIXTURE_SAMPLE_MODE_OFF`
  re-export.
- `frontend/src/features/dashboard/useSampleMode.ts` /
  `useSampleMode.test.tsx` â€” delete both (also listed in "Delete these files
  entirely" above; unchanged since STORY-049 despite STORY-056 moving its
  callers).
- `frontend/src/AppShell.tsx` â€” remove the `useSampleMode` import + its call,
  the derived `bannerVisible` boolean, the `sampleMode={sampleMode}` prop
  passed to `TopBar`, and the `<SampleModeBanner visible={bannerVisible} />`
  render call (STORY-056 seam â€” `AppShell` reverts to composing `Sidebar` +
  `TopBar` (no prop) + the routed `<main>` only).
- `frontend/src/nav/TopBar.tsx` / `TopBar.css` / `TopBar.test.tsx` â€” remove
  the `sampleMode: UseSampleModeResult` prop and every trigger-button branch
  keyed off it (the `mutationError` alert, the `state.phase === 'success'`
  switch, the `state.phase === 'error'` retry button, and their CSS); `TopBar`
  reverts to rendering only the theme toggle (STORY-056 seam).
- `frontend/src/nav/SampleModeBanner.tsx` / `SampleModeBanner.css` /
  `SampleModeBanner.test.tsx` â€” delete all three (STORY-056 seam; nothing
  else in `AppShell` depends on this component once its render call above is
  removed).
- `frontend/src/pages/DashboardPage.tsx` / `.css` / `.test.tsx` â€” nothing to
  revert here anymore as of STORY-056 (the inline `SampleModeToggle`
  component/CSS/tests were already removed from this page when the trigger
  relocated to the shell; this bullet is now a no-op, kept only so a future
  reader doesn't wonder why the sprint-32 removal recipe used to name this
  file and no longer does).

**DynamoDB partition cleanup:** the `sample_mode` table has been retired and is now stored in the control table under the `SAMPLE_MODE` partition. For removal, we simply delete the `SAMPLE_MODE` row and delete the corresponding repository.


**Data cleanup:** any simulated rows already written to a real `observations`
table are identifiable by the D5 sentinel â€” `WHERE raw_ref LIKE
'sample-mode%'` â€” for manual cleanup/deletion if desired; removing the code
does not retroactively touch already-persisted rows.

**What is untouched by removal** (D7 â€” never had a seam in the first place):
`core/domain/*`, `core/services/*`, `composition/pull_loop.py`,
`composition/seed_dynamo.py`, all pre-existing tables, all pre-existing
backend endpoints, and â€” on the frontend side (STORY-049) â€” every OTHER
tab/feature (`useComponents`, `useApprovals`, `useAvailability`,
`AvailabilityPage`, `ApprovalsPage`), `lib/useFetch.ts` itself (unchanged),
and `mocks/handlers/{components,approvals,availability}.ts`. The
publisher/approval chain needs no change either way â€” sample mode only ever
produced ordinary data flowing through it.

## History
- sprint-43 (STORY-078, unrelated story â€” mechanical staleness sweep only): this article's
  `code_refs` include `pyproject.toml`, which changed only in the `core-internal-layering`
  contract (added the `src.core.queries` layer for the CQRS-lite move â€” unrelated to the
  `api-feature-independence` `sample_mode` entry). No Facts changed. verified_sha = 6859f17.
- sprint-42 (STORY-075, unrelated story â€” mechanical staleness sweep only): this article's
  `code_refs` include `backend/src/composition/app.py`, which changed only cosmetically â€” a
  ruff-inserted blank line before the STORY-075 `install_error_handlers(app)` call (the
  centralized error-registry wiring, see [[api-five-file-convention]]). The `sample_mode_repo`
  param/wiring Facts and the REMOVAL recipe's `app.py` bullet are untouched. No Facts changed.
  verified_sha = 3ea7e31.
- sprint-38 (STORY-056, Wave 1 of the Operator Dashboard redesign â€” the app shell): relocated the
  frontend consumer OUT of `DashboardPage` and into the shell (see the rewritten "The frontend
  consumer" section above). `features/dashboard/useSampleMode.ts` itself is BYTE-IDENTICAL â€” only
  its caller changed, from `DashboardPage`'s embedded `SampleModeToggle` to `AppShell.tsx` calling
  it once and threading the result down to the new `nav/TopBar.tsx` (the âš¡ trigger) and
  `nav/SampleModeBanner.tsx` (the now-dismissible warning). `DashboardPage.tsx`/`.css`/`.test.tsx`
  lost all sample-mode content; the equivalent test coverage now lives in `TopBar.test.tsx` /
  `SampleModeBanner.test.tsx` / `AppShell.test.tsx` (moved, not dropped). Rewrote the REMOVAL
  recipe's frontend bullets to match (new `AppShell.tsx`/`TopBar.tsx`/`SampleModeBanner.tsx` seam
  points; the old `DashboardPage.*` bullets are now no-ops, kept as a pointer rather than deleted).
  `code_refs` += `frontend/src/AppShell.tsx`, `frontend/src/nav/TopBar.tsx`,
  `frontend/src/nav/SampleModeBanner.tsx`; removed `frontend/src/pages/DashboardPage.tsx`/`.css`
  (no sample-mode content left in either). Frontend-only; six backend gates untouched (empty diff
  since `sprint-38-start`). verified_sha = 4daf4c6.
- sprint-37 (STORY-046, unrelated story â€” mechanical staleness sweep only): this article's
  `code_refs` include `frontend/src/pages/DashboardPage.tsx` and `frontend/src/pages/
  DashboardPage.css`, both of which changed for STORY-046 (the Dashboard maintenance
  indicator â€” see [[frontend-zone]]), but ONLY additively: a new `useMaintenanceWindows`
  import/call, a page-local `isUnderActiveMaintenance` helper, and a second `StatusBadge`
  rendered in the Status cell, plus a new `.dashboard-status-cell` CSS rule. None of it
  touches the `useSampleMode` import, the `SampleModeToggle` component, its
  `<SampleModeToggle />` render call, or the `.dashboard-sample-mode*` CSS block â€” re-checked
  the REMOVAL recipe above line-by-line, it still names exact sample-mode-only lines/blocks
  in each file, none of which moved. No Facts changed. verified_sha = 0f42798.
- sprint-36 (STORY-047, quality-review minors chore): AC5 parametrized
  `FakeSampleModeRepository`'s store hint from bare `dict` to `dict[str,
  bool]` (Fact updated above) â€” cosmetic, no behavior change. This article's
  `code_refs` also include `backend/src/composition/app.py`, which changed
  for AC1 (the injected-fakes publisher-wiring fix, unrelated to
  `sample_mode_repo` wiring â€” see [[api-five-file-convention]] and
  [[statuspage-publish]]); the `sample_mode_repo` param/wiring Facts above
  are untouched. No other Facts changed. verified_sha = d441468.
- sprint-36 (STORY-043, unrelated story â€” mechanical staleness sweep only): this article's
  `code_refs` include `backend/src/composition/run.py` and `pyproject.toml`. `run.py` gained ONE
  unrelated line â€” a `load_dotenv()` call at the top of `main()`, before
  `load_settings`/`load_live_secrets` run (a `.env`-loading defect fix; see
  [[dev-setup-and-dod]] and [[ingest-service-and-pull-loop]]) â€” the marked STORY-048 seam
  (`build_live_loop` step 2's `SampleModeIngest` wrap) is untouched. `pyproject.toml` gained
  `python-dotenv` in `[project.dependencies]`, unrelated to the `api-feature-independence`
  contract's `sample_mode` entry. No Facts changed. verified_sha = 6a33edb.
- sprint-36 (STORY-050, unrelated story â€” mechanical staleness sweep only): this article's
  `code_refs` include `backend/tests/test_run_live_loop.py`, which gained one new test
  (`test_main_fails_fast_on_missing_secrets_before_any_loop_starts`, pinning STORY-050's AC2) â€”
  purely additive, no assertion on `SampleModeIngest`/`build_live_loop` touched or added; the
  removal inventory's mention of `test_run_live_loop.py` (the `test_build_live_loop_assembly`
  revert instructions) remains accurate as written. No Facts changed. verified_sha = 80df0c2.
- sprint-34 (STORY-015f, unrelated story â€” mechanical staleness sweep only): the same three
  `code_refs` (`frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
  `frontend/src/mocks/handlers/index.ts`) changed again, but ONLY additively â€” STORY-015f (the
  Maintenance tab) added its own `MaintenanceWindowDTO`/`CreateMaintenanceRequest`,
  `getMaintenance`/`postMaintenance`, and `maintenanceHandlers` import/spread alongside the
  existing sample-mode content in those same shared files. `client.ts` also gained an optional
  `ApiError.detail` field (populated from any non-2xx `{"detail": ...}` body, not just
  sample-mode's) â€” purely additive to the `ApiError` shape, does not touch `getSampleMode`/
  `putSampleMode`/`putJson` themselves. Re-checked the REMOVAL recipe above line-by-line: it still
  names exact sample-mode-only lines/blocks in each file, none of which moved or were touched by
  STORY-015f; `putJson` is still adopted by no other endpoint (STORY-015f's `postMaintenance` uses
  `postJson`), so that removal caveat remains accurate too. No Facts changed. verified_sha =
  e86493f.
- 2026-07-06 (debug sprint, no story â€” `docs/scrum/sprints/2026-07-06-debug-sample-mode/
  report.md`): added the "Operational gotchas" section after a PO report ("sample mode ON
  but Check History shows up") was root-caused as environmental, not a code defect. The
  full chain (PUT â†’ flag row â†’ per-cycle read â†’ forced-DOWN ingest â†’ history API) was
  live-verified BOTH ways against real Grail on branch
  `debug/sample-mode-forced-down-not-applied`: flag ON â†’ 120/120 + 2/2 rows `down` with
  the D5 sentinel across two advancing-watermark cycles; flag OFF â†’ subsequent rows
  genuine `up`, `raw_ref` NULL. No Facts changed â€” the gotchas make explicit what D4's
  dedup-unchanged fact already implied operationally. verified_sha = 1257cc9.
- sprint-33 (STORY-015g, unrelated story â€” mechanical staleness sweep only): the same three
  `code_refs` (`frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
  `frontend/src/mocks/handlers/index.ts`) changed again, but ONLY additively â€” STORY-015g (the
  Publications tab) added its own `PublicationDTO`, `getPublications`, and `publicationsHandlers`
  import/spread alongside the existing sample-mode content in those same shared files, none of
  which moved or were touched. Re-checked the REMOVAL recipe above line-by-line: it still names
  exact sample-mode-only lines/blocks in each file; still accurate as written. No Facts changed.
  verified_sha = b7811cf.
- sprint-33 (STORY-015e, unrelated story â€” mechanical staleness sweep only): three of this
  article's `code_refs` (`frontend/src/api/types.ts`, `frontend/src/api/client.ts`,
  `frontend/src/mocks/handlers/index.ts`) changed, but ONLY additively â€” STORY-015e (the Check
  History tab) added its own `ObservationDTO`, `getHistory`, and `historyHandlers` import/spread
  alongside the existing sample-mode content in those same shared files. Re-checked the REMOVAL
  recipe above line-by-line: it still names exact sample-mode-only lines/blocks in each file, none
  of which moved or were touched by STORY-015e, so the recipe remains accurate as written. No Facts
  changed. verified_sha = 0a1ef52.
- sprint-32 (STORY-049): updated. Landed the frontend consumer â€” the
  Dashboard sample-mode toggle (see the new "The frontend consumer" section
  above) â€” and extended the REMOVAL inventory with every frontend
  file/seam it added (`useSampleMode.ts`/`.test.tsx`, `mocks/handlers/
  sampleMode.ts`, and the shared-file edits to `api/types.ts`, `api/
  client.ts` (+ the new `putJson` helper), `api/client.test.ts`,
  `mocks/handlers/index.ts`, `pages/DashboardPage.{tsx,css,test.tsx}`).
  Corrected the D7 "untouched by removal" list, which previously (wrongly,
  as of this story) named "the frontend" wholesale. `code_refs` +=
  the seven frontend files above. Frontend-only change; six backend gates
  untouched-green (empty diff â€” no backend source change), three frontend
  gates green. verified_sha = 63886bc.
- sprint-31 (STORY-048): created. PO directive at lock, 2026-07-03: a
  TEMPORARY feature; removability is a first-class AC (AC7). D1â€“D7 pinned in
  `docs/scrum/sprints/2026-07-03-sprint-31/plan.md`. verified_sha â†’ 0ea652e
  (the last code commit before this article; T1â€“T5 landed as five separate
  TDD commits, each touching only dedicated new files plus the marked seam
  points named above).
- sprint-41 (STORY-070): re-verified. `run.py::main` gained a vendor-id drift probe call at startup
  and `test_run_live_loop.py` gained one wiring test (see [[ingest-service-and-pull-loop]]); neither
  touches the `SampleModeIngest` seam or the sample-mode wiring this article describes. No Fact
  changed. verified_sha â†’ 4d3fd7a.
- sprint-44 (STORY-079, Facts-coverage cleanup): `yt_wiki.py facts` flagged three uncovered
  citations: `frontend/src/pages/DashboardPage.tsx` (the Fact stating it no longer imports/renders
  anything sample-mode-related), `backend/tests/test_ingest_service.py` and
  `backend/tests/test_pull_loop.py` (the "pre-existing BEHAVIOR tests... were NOT touched" Fact in
  the seam section â€” note that Fact's own subordinate clause, "neither file appears in this
  article's `code_refs` because neither changed," described a v1-era convention where only
  in-story-changed files were added; the v2 facts-coverage lint supersedes that convention â€” a Fact
  citing a file must be covered by `code_refs` regardless of whether the story changed it, so both
  are added here even though the substantive claim, that they were untouched, remains true and
  unedited). Added to `code_refs`. No Fact text changed. verified_sha â†’ 678ff0d.
- sprint-44 (STORY-079 fix loop, quality review MAJOR / spec review non-blocking finding, both
  converging on this fix): the seam-section clause "neither file appears in this article's
  `code_refs` because neither changed" went stale the moment this same story's Facts-coverage pass
  (above) added `backend/tests/test_pull_loop.py` and `backend/tests/test_ingest_service.py` to
  `code_refs` â€” the clause then contradicted the frontmatter it sat next to. Deleted the clause;
  the durable claim it was attached to (both files "were NOT touched and pass unmodified") is
  unedited and remains true. `verified_sha` re-stamped to `adc002a`.
- sprint-45 (STORY-065/STORY-066): re-verified, no changes to Sample Mode. verified_sha -> f6f589fd4dcb6e3a2a565453c43b0fb95d7e5787.

- 2026-07-13 (sprint-45 gate closure): re-stale was ruff-format-only (48fba51 line-wrapped a delete stmt + trimmed trailing blank lines in maintenance_repository.py / fakes.py / test_persistence_adapters.py) â€” behavior and Facts unchanged. Re-verified; verified_sha -> 010a21b.
- sprint-46 (STORY-082): Re-verified after pyproject.toml changes. verified_sha -> abd8609.
- sprint-50 (STORY-093, test hygiene): `test_run_live_loop.py::test_main_resource_lifecycle_success`
  gained real assertions on the mocked resource-lifecycle surface; the sample-mode
  wiring (`SampleModeIngest`, `DynamoSampleModeRepository`) it exercises is UNCHANGED. No Fact
  changed. verified_sha -> a8700f5.
- sprint-51 (STORY-094, mechanical staleness sweep): `frontend/src/api/client.ts` (in this
  article's `code_refs` as a shared file) changed only in the unrelated `getHistory` docstring
  (a comment noting the server's new optional `limit` cap, see [[frontend-zone]] and
  [[api-five-file-convention]]) - `getSampleMode`/`putSampleMode` and every Sample Mode Fact
  in this article are untouched. No Fact changed. verified_sha -> d0f6573.
- sprint-55 (STORY-103, PO-ordered full UI rewrite): checked the frontend Facts against what
  survives on the new `sprint-55`/`ui-rewrite` line, per the story's wiki-ownership brief - this
  was NOT a trivial re-verify: `nav/TopBar.tsx`, `nav/SampleModeBanner.tsx`, and
  `pages/DashboardPage.tsx` were all DELETED (old-skin removal, see [[frontend-zone]]), and the
  new minimal `AppShell.tsx` no longer calls `useSampleMode()` at all - the frontend sample-mode
  switch/banner surface is temporarily ABSENT from the app until STORY-104 re-wires the still-green
  `useSampleMode.ts` hook into the new shell. Added a "CURRENT STATE" subsection documenting this;
  the STORY-049/056 Facts above it are left as an accurate historical record of the last working
  integration. `code_refs` dropped the three deleted paths (`nav/TopBar.tsx`,
  `nav/SampleModeBanner.tsx`, `pages/DashboardPage.tsx`); `AppShell.tsx` kept (still exists,
  rewritten). verified_sha -> 52f1706.
- sprint-55 (STORY-104, restores the frontend surface on the new shell): rewrote the "CURRENT
  STATE" subsection - the switch/chip/banner trio is live again, on new files
  (`nav/SampleModeSwitch.tsx`, `nav/SampleModeChip.tsx`, a NEW `nav/SampleModeBanner.tsx` at the
  same path the STORY-103-deleted one used to occupy, `nav/useDismissibleBanner.ts`), all ported
  in BEHAVIOR from the parked `ui-redesign` branch's STORY-056/102 versions per the story's
  salvage-list instruction, re-skinned onto Mission Teal tokens. `AppShell.tsx` calls
  `useSampleMode()` once again and threads it to the new `nav/CommandBar.tsx` + the restored
  banner. `useSampleMode.ts` itself remains untouched throughout. `code_refs` +=
  `nav/SampleModeSwitch.tsx`, `nav/SampleModeChip.tsx`, `nav/SampleModeBanner.tsx` (re-added),
  `nav/useDismissibleBanner.ts`. Frontend-only; six backend gates untouched (empty diff). Suite:
  461 tests / 57 files, all green. verified_sha -> 5dd72ce.
