# Sprint 31 — Plan

**Dates:** starts 2026-07-03.
**Goal:** an on-demand outage simulator (STORY-048) — DB-persisted sample-mode flag (default
OFF), API toggle, live loop records incoming observations as DOWN while ON. **TEMPORARY feature
by PO directive: removability is a first-class AC (AC7).** Frontend toggle is STORY-049, NOT
this sprint.
**Branch:** `sprint-31` (tag `sprint-31-start` @ `5914c45`). Committed: 5 pts (velocity mean
4.3; the proven single-5 shape; PO approved "lock story 048" + the temporary-feature directive,
2026-07-03).
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers
(5 pts → full pipeline).

This is a BACKEND story. Work is under `migrations/versions/`, `backend/src/core/ports/`,
`backend/src/adapters/persistence/`, `backend/src/composition/` (new decorator module + ONE
marked seam line in `run.py` + `app.py` wiring), `backend/src/api/` (one NEW five-file module),
and tests under `backend/tests/`. **No frontend change. No change to core services or domain
types** (`core/domain/signal.py` in particular stays byte-identical — see D5). The six backend
DoD commands must stay green.

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green
step**, staging only touched files (never `git add -A`), branch verified `sprint-31` before each
commit. DB-gated tests use the shared `migrated_db` fixture; NEVER run two DB-gated pytest
invocations concurrently against one throwaway DB (2026-07-02 agreement).

## The removability directive (PO, 2026-07-03 — shapes every decision below)

This feature WILL be deleted some day. Therefore: all new logic in dedicated new files; existing
files touched only at minimal seam points, each marked with a `# STORY-048 sample-mode seam
(temporary — see docs/scrum/wiki/sample-mode.md)` comment; no changes to canonical domain types
or existing tables; with the flag OFF the system is byte-identical to today. Every decision that
had a "more integrated" alternative deliberately picks the more removable one.

## Key facts (verified against code, 2026-07-03)

- **The two-process constraint:** the API server (`composition/app.py::create_app`) and the live
  loop (`composition/run.py`) share ONLY the database. The flag must be DB-persisted; the loop
  must re-read it per cycle.
- `core/ports/signal_ingest.py::SignalIngestPort` — ONE abstract method
  `ingest_observations(batch: Sequence[SignalObservation]) -> IngestResult`. The live loop's
  ingest chain (`run.py::build_live_loop` step 2) builds `ingest_port = IngestService(
  observation_repo=..., watermark_repo=..., rejected_repo=..., clock=...)` and hands it to each
  `run_periodic(...)` — each cycle calls `ingest_observations` ONCE. This is THE seam: a
  decorator wrapping `ingest_port` is one changed line in `run.py`.
- `core/domain/signal.py::SignalObservation` — frozen Pydantic; fields incl. `health: Health`
  (`UP|DOWN|DEGRADED`) and `raw_ref: str | None = None` ("pointer to the archived raw payload;
  the core never reads it"). `raw_ref` IS persisted (`observations.raw_ref Text nullable`,
  spine migration line 163; `adapters/persistence/observation_repository.py` writes and reads
  it) and is `None` for every live http-path row today (only the clickpath normalizer ever set
  it). The history API deliberately OMITS it from the client DTO (`api/v1/history/models.py`).
  Frozen models support `model_copy(update={...})`.
- `composition/app.py::create_app` — injection pattern: optional port kwargs, real branch builds
  Postgres impls from the shared engine, everything lands on `app.state.<name>`;
  `api/dependencies.py` has one `get_<name>` provider per port. Sprint 30 added
  `signal_repo` following exactly this pattern — mirror it.
- Migrations head: `5ed254a8daab` (sprint 30's `add_signals_interval_seconds`) — the new
  revision chains from it.
- Five-file convention + shape test; api-feature-independence contract module list in
  `pyproject.toml` must gain the new module (sprint 30 added `src.api.v1.topology` — mirror).
- `backend/tests/fakes.py` — shared fakes home (FakeSignalRepository etc. live there).
- `backend/tests/test_run_live_loop.py` — asserts the REAL assembled wiring of
  `build_live_loop` (2026-06-29 assembly-test agreement). Adding the decorator changes the
  asserted shape — this test is UPDATED (the sanctioned exception in AC7b); the ingest-service
  and pull-loop BEHAVIOR tests must pass unmodified.

## Design decisions (pinned — do not improvise; 2026-06-26 plan-edge-behavior agreement)

**D1 — Storage: a dedicated single-row `sample_mode` table (droppable; no FK; no existing table
touched).** New Alembic revision (down_revision `5ed254a8daab`):
`sample_mode(id BOOLEAN PRIMARY KEY DEFAULT TRUE CHECK (id), enabled BOOLEAN NOT NULL,
updated_at TIMESTAMPTZ NOT NULL DEFAULT now())` — the CHECK pins the table to at most one row.
Downgrade drops the table. NO seed change (never-set → the port's default handles it, D2). No
FK in either direction — `check_fk_direction.py` unaffected. Removal = one drop-table migration.

**D2 — Port: `core/ports/sample_mode_repository.py::SampleModeRepository(ABC)`.** Two methods,
edge behaviors explicit:
- `is_enabled() -> bool` — the current flag; **no row ever written → `False`** (the PO's
  default-OFF lives HERE, not in a seed). Never raises on empty.
- `set_enabled(enabled: bool) -> None` — idempotent upsert of the single row (INSERT ... ON
  CONFLICT (id) DO UPDATE SET enabled=excluded.enabled, updated_at=now()). Setting the current
  value again succeeds silently.
No new domain type (the payload is a bare bool), no new domain error (no not-found case exists).
Export via `core/ports/__init__.py`. `adapters/persistence/sample_mode_repository.py::
PostgresSampleModeRepository(engine)` mirrors peers. `FakeSampleModeRepository` in
`backend/tests/fakes.py`. ONE parity contract test body against BOTH impls (Postgres half
DB-gated via `migrated_db`): never-set → False; set True → True; set False → False; set same
value twice → no error (idempotent); state survives a fresh repository instance on the same
engine (proves persistence, not instance memory).

**D3 — API: new five-file module `api/v1/sample_mode/`, path `/sample-mode`.**
- `GET /sample-mode` → `SampleModeDTO{enabled: bool}` (reads `is_enabled()`).
- `PUT /sample-mode` with body `{"enabled": true|false}` → applies `set_enabled`, returns the
  new `SampleModeDTO`. Idempotent. Missing/invalid body field → 422 (Pydantic request model
  `SampleModeUpdateRequest{enabled: bool}` — FastAPI's validation; `validation.py` mirrors the
  trivial-validator pattern since there is nothing syntactic beyond the typed body).
- DTOs frozen; DI provider `get_sample_mode_service` in the feature's `service.py`; controller
  import-clean; five-file shape test (set equality) is a NAMED deliverable (2026-06-28).
- Wiring: `sample_mode_repo: SampleModeRepository | None = None` param on `create_app`
  (real branch builds Postgres impl — mark the wiring lines with the STORY-048 seam comment;
  injected branch leaves as-passed), `app.state.sample_mode_repo`, `get_sample_mode_repo` in
  `api/dependencies.py`, router registered in `api/v1/__init__.py`, module added to the
  api-feature-independence contract list in `pyproject.toml`.
- Tests: fake-injected GET default False, PUT true → GET true, PUT false → GET false, PUT
  garbage/missing body → 422; ONE DB-gated round-trip (real create_app against `migrated_db`:
  PUT true, fresh GET reads true from Postgres).

**D4 — The override: `composition/sample_mode.py::SampleModeIngest(SignalIngestPort)` — a
composition-layer decorator; ONE marked seam line in `run.py`.**
Constructor `(delegate: SignalIngestPort, sample_mode_repo: SampleModeRepository)`.
`ingest_observations(batch)`:
1. `enabled = self._sample_mode_repo.is_enabled()` — read ONCE per call. Each `run_periodic`
   cycle calls ingest once, so this IS the per-cycle read (AC4) — no caching, no TTL, no
   background refresh. A repo read failure PROPAGATES (the cycle already depends on the same
   DB; never swallow — consistent with the loop's existing cycle-failure handling).
2. `enabled is False` → `return self._delegate.ingest_observations(batch)` with the batch
   object UNTOUCHED (same instances — AC7b byte-identical).
3. `enabled is True` → delegate a transformed batch: each observation replaced by
   `obs.model_copy(update={"health": Health.DOWN, "raw_ref": SIMULATED_RAW_REF})` — everything
   else (signal_key, observed_at, source_event_id, provenance, location, latency_ms) unchanged,
   so idempotent dedup and watermarks behave identically.
`run.py::build_live_loop` step 2 becomes (the ONLY run.py change, seam-commented):
`ingest_port = SampleModeIngest(delegate=IngestService(...), sample_mode_repo=
PostgresSampleModeRepository(engine))`.
Empty batch: pass through to the delegate exactly as today regardless of flag state (transform
of `[]` is `[]`; no special case — and the existing empty-batch behavior stays the delegate's).
Do NOT wire the decorator into `create_app`'s publisher/approval path — the API process ingests
nothing; its only sample-mode surface is D3.

**D5 — The simulated marker (AC5): `raw_ref` sentinel, ZERO schema/domain change.**
`SIMULATED_RAW_REF = "sample-mode:forced-down"` — a module-level constant in
`composition/sample_mode.py`, docstring-documented. Why `raw_ref`: it is already persisted and
round-tripped by the observation repository, it is `None` on every genuine live http row, the
core never reads it, and the history API never exposes it — so a simulated row is mechanically
distinguishable (`raw_ref = 'sample-mode:forced-down'` / SQL `WHERE raw_ref LIKE
'sample-mode%'`) while NOTHING else in the system changes. The alternative (a `simulated`
column/field) would touch the canonical domain type + table + every constructor — exactly what
the removability directive forbids. AC5's test: with the flag ON, the persisted row has
`health == DOWN` AND `raw_ref == SIMULATED_RAW_REF`; a genuine DOWN (flag OFF, vendor reports
down) has `raw_ref is None` — the two are distinguishable.

**D6 — REMOVAL inventory: new wiki article `docs/scrum/wiki/sample-mode.md` (AC7c).**
Frontmatter per the wiki protocol (`code_refs` = the new files + the seam-touched files,
`verified_sha` = final commit). Facts: what the feature does, flag semantics (default OFF,
per-cycle read), the marker sentinel. Plus a **REMOVAL** section listing exactly: the files to
DELETE (`composition/sample_mode.py`, `api/v1/sample_mode/` ×5, `core/ports/
sample_mode_repository.py`, `adapters/persistence/sample_mode_repository.py`, the fake, the
story's test files), the marked seam lines to REVERT (`run.py` ingest wrap, `create_app` +
`dependencies.py` + `api/v1/__init__.py` + `pyproject.toml` entries — grep `STORY-048` finds
them), the DROP migration to write, and this article's own archival. Also: simulated rows
already in a database are identifiable by the D5 sentinel for cleanup.

**D7 — What explicitly does NOT change.** `core/domain/*` (especially `signal.py`),
`core/services/*` (ingest_service, pipeline, decide, availability — the override wraps, never
edits), `composition/pull_loop.py`, `composition/seed.py`, all existing tables and migrations,
the frontend, all existing endpoints. The publisher/approval chain is untouched — a simulated
outage flows through it as ordinary data, which is the entire point.

## STORY-048 — sample switch backend (5 pts) — AC1–AC7

- [x] **T1 — Migration + port + adapter + fake parity (D1, D2; AC1), TDD.** Failing parity
      contract test first (ONE body, both impls; Postgres half DB-gated): never-set → False,
      set/read round-trips, idempotent re-set, persistence across repository instances. Then:
      the migration (docstring names STORY-048 + TEMPORARY + the paired removal expectation),
      the port (edge behaviors in docstrings), the Postgres adapter, the fake in
      `backend/tests/fakes.py`.
- [x] **T2 — Five-file `api/v1/sample_mode/` + wiring (D3; AC2), TDD.** Failing tests first:
      shape test; GET default false; PUT→GET round-trips (fake-injected); 422 on bad body;
      DB-gated round-trip. Then the module + `create_app`/`app.state`/`dependencies.py`/
      `api/v1/__init__.py`/`pyproject.toml` wiring (seam comments on the create_app lines).
- [x] **T3 — `SampleModeIngest` decorator (D4, D5; AC3, AC5), TDD.** Failing tests first (all
      fake-driven — fake delegate capturing batches, fake flag repo): OFF → delegate receives
      the IDENTICAL batch objects (assert identity, not equality — AC7b); ON → delegate
      receives copies with `health=DOWN` + `raw_ref=SIMULATED_RAW_REF` and ALL other fields
      unchanged (assert signal_key/observed_at/source_event_id/location/latency_ms/source
      equality); ON with a vendor-DOWN observation → still DOWN + marker (no double-flip
      weirdness); empty batch passes through under both states; repo-read failure propagates
      (fake raising → decorator raises). AC5 distinguishability: simulated row vs genuine DOWN
      differ on `raw_ref`. Then implement the decorator (module docstring: TEMPORARY, dossier
      §6/§8 seam, the removal pointer).
- [x] **T4 — The run.py seam + per-cycle flip (D4; AC3, AC4), TDD.** Failing tests first:
      UPDATE `test_run_live_loop.py`'s assembly assertions — `build_live_loop` now yields
      `run_periodic` kwargs whose `ingest_port` is a `SampleModeIngest` whose `_delegate` is
      the real `IngestService` wired to the real repos (2026-06-29 agreement: assert the REAL
      nesting, mock only genuine I/O edges; this update is the AC7b sanctioned exception —
      justify it in the report). AC4 two-cycle test: drive ingest twice against a fake flag
      repo flipped between calls (OFF→ON: first batch recorded as-is, second forced DOWN;
      ON→OFF symmetric) — proving a flip takes effect next cycle with no rebuild. Then the
      one-line `run.py` change with the seam comment. Pre-existing ingest-service + pull-loop
      BEHAVIOR tests pass UNMODIFIED (run them; name them in the report).
- [x] **T5 — End-to-end proof (AC3/AC5 integration).** One fake-driven end-to-end: observations
      flow through the REAL `IngestService` (fake observation/watermark/rejected repos or the
      DB-gated harness — cheapest honest path) wrapped by the decorator with the flag ON →
      persisted rows are DOWN + marked; flag OFF → rows match the vendor payload. This is the
      story's reason-to-exist regression.
- [x] **T6 — Gates + wiki + REMOVAL inventory (D6; AC6, AC7).** *(wiki tail recovered from the
      stalled implementer + committed by the orchestrator as 61d786a per the 2026-06-25
      crash-recovery agreement; six-command gate orchestrator-run at 61d786a — all exit 0,
      pytest 498 passed single run; sweep 13/13 CURRENT)* All six backend DoD commands
      exit 0 on a clean committed tree — SINGLE non-concurrent DB-gated run. CLAUDE.md:
      command-sync N/A (no command changes; do NOT add feature docs to CLAUDE.md — the wiki
      article is the home). Write `docs/scrum/wiki/sample-mode.md` (Facts + REMOVAL inventory,
      symbol-cited). Resolve blast radius via the mechanical sweep over ALL articles — do not
      hand-pick (2026-06-28 agreement; expect drift wherever your diff touches existing
      `code_refs`, e.g. run.py, pyproject.toml, fakes/conftest — the sweep decides). Bump
      `verified_sha`s; REPORT which articles you touched.

## Conventions checklist (held at quality review)
- Module + public-symbol docstrings citing the relevant dossier § (peers set the register);
  the decorator + migration docstrings additionally say TEMPORARY + point at the removal
  inventory.
- Every existing-file edit carries the `STORY-048 sample-mode seam` comment (AC7a — grep-able).
- Frozen DTOs; no cross-field invariants expected (bare bool) — if you add a type with one,
  `model_validator(mode="after")` + both-shapes tests (2026-06-26).
- Empty-input tests where applicable (2026-06-25): empty batch through the decorator, never-set
  flag.
- Fake/adapter parity via ONE contract body (2026-06-26); check-then-act N/A (upsert, no
  guarded write).
- Assembly tests assert REAL wiring; only genuine I/O edges mocked (2026-06-29).
- A contract change REWRITES covering tests (`test_run_live_loop.py` assembly shape) — never
  deletes to a gap (2026-06-29); BEHAVIOR tests stay unmodified (AC7b).
- Five-file shape test for `sample_mode/` (2026-06-28); DTO maps values directly, no sentinel
  fallbacks (2026-06-28); no datetime inputs on the new endpoints (tz-agreement N/A).
- Scoped staging; commit-after-green; no `git add -A`; ruff-clean before each commit.
- Import boundaries: port in core (imports nothing outward); adapter imports core only;
  decorator lives in composition (may import core + adapters); the api feature imports core
  ports + its own files; `lint-imports` stays 5 kept / 0 broken.

## Guardrails (implementer)
- Build to THIS plan + `docs/scrum/stories/STORY-048-sample-switch-simulate-down.md` + dossier
  §6/§8/§13/§17 — never chat history. D1–D7 are BINDING; genuine conflict with the code you
  find → STOP and report, don't improvise.
- The removability directive is a PO order: if any step tempts you to edit a core domain type,
  an existing table, or an existing core service — STOP; the plan has a removable alternative.
- Do NOT write `.scrum/` board state (plan.md checkbox ticks are the one exception); do NOT run
  reviewers or merge. No live credentials needed (fakes + throwaway DB prove everything).
- Genuine ambiguity → STOP with the exact question. Effort > 3× the 5-pt estimate → STOP.
- Report: steps done + commit SHA each; every gate command + exit code + output tail; the named
  BEHAVIOR test files that passed unmodified; wiki articles touched; net-new/rewritten/deleted
  tests with justification; anything noticed-but-not-done.

## Sequencing rationale
T1 first — the persisted flag is the foundation and carries the parity risk. T2 exposes it over
HTTP (pure edge, mirrors sprint-30's T3 pattern). T3 is the feature's heart, built fake-first
against the port from T1. T4 threads it into the real loop assembly (the one existing-file seam,
riskiest for AC7b). T5 proves the story end-to-end. T6 gates + the removal inventory that makes
the PO's temporary-feature directive durable. Risk lives in the assembly-test update (T4) and in
scope discipline — the removability constraint is satisfied by SUBTRACTION (touch less), which
the plan enforces by naming every allowed seam.
