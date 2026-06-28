# Sprint 15 — Plan

**Goal:** Finish the ready backend — per-signal Availability + Check History read endpoints
(completing the Zone 6 read API) — and make the DB-gated test suite robust on a reused DB.

**Branch:** `sprint-15` · **Start tag:** `sprint-15-start` · **Baseline:** `b665c6b` (refinement on
branch; from main `37c7dd5`).

**Committed: 5 pts** — STORY-014c (3) → STORY-039 (2), in that order.

---

## How this sprint runs (external implementation — working-agreements.md 2026-06-26)
The PO implements this plan externally onto `sprint-15`; the orchestrator does NOT dispatch
implementers (but may finish via a **Sonnet** implementer subagent if the PO's quota runs out, as in
Sprint 14). This `plan.md` is the only contract — self-contained. When ready, say **"do your
review"**; the orchestrator diffs `sprint-15-start..HEAD`, runs the full six-command gate, runs the
Opus spec + quality reviewers on STORY-014c, resolves the wiki blast radius, then
review → verdict → merge → retro. **TDD + commit-after-green. Scoped staging only. Do NOT write
`.scrum/` board state.**

### The six-command DoD gate — exit 0 each
`pytest` · `lint-imports` (**5 kept / 0 broken** — `availability`+`history` added to
`api-feature-independence`; count stays 5) · `python scripts/check_fk_direction.py` ·
`alembic upgrade head` · `ruff check .` · `ruff format --check .`. DB-gated: `scripts/dev_db.py up` →
run → `down`. **No new migration this sprint.**

### Established facts the implementer builds on
- Five-file feature pattern + wiring: copy `api/v1/components` + `api/v1/maintenance` (controller
  imports only its models+service; DI provider in the feature `service.py`; register the router in
  `src/api/v1/__init__.py`; add `get_*_repo`/dependency in `src/api/dependencies.py`; add a param +
  `app.state` entry in `composition/app.py::create_app`, left-as-passed in the injected branch — do
  NOT import `tests`).
- `core/services/availability.py::AvailabilityCalculator(observation_repo=...)`; its method is
  `compute(signal_key, *, since, until, interval, window, maintenance, computed_at) -> AvailabilityResult`.
  `AvailabilityResult` fields: `availability_pct: float|None`, `completeness_pct: float|None`,
  `total_verdicts`, `passing_verdicts`, `maintenance_verdicts`, `gap_verdicts`, `distinct_locations`,
  `window: str`, `computed_at: datetime`.
- `core/ports/observation_repository.py::ObservationRepository.in_window(signal_key, since, until)`
  returns `SignalObservation`s. `SignalObservation` fields: `signal_key`, `observed_at`, `health`,
  `source_event_id`, `source` (Provenance), `location`, `latency_ms`, `raw_ref`.
- `FakeObservationRepository` is in `backend/tests/fakes.py`. The clock is in `app.state.clock`
  (`get_*` via dependencies); `ClockPort.now()` gives "now".

---

## STORY-014c — Availability + Check History read endpoints (3 pts) — DO FIRST

Pipeline: **gate + Opus spec & quality reviewers.** Pure reads (TOCTOU N/A). PER-SIGNAL.

### Required-input note (read carefully — `compute` needs more than the query)
`compute` requires an `interval` (cadence) and a `maintenance: Callable[[datetime], bool]`. Per-signal
we do not have these from config yet (deferred to STORY-040). Resolve them at the edge as documented
stopgaps:
- `interval` → query param `interval_seconds: int` (optional, **default 60**); pass as
  `timedelta(seconds=interval_seconds)`.
- `maintenance` → a no-op `lambda _at: False` (per-signal cannot resolve a component's maintenance
  until the signal→component mapping exists). Document this limitation in the service docstring.
- `window` label → the human window string (e.g. `"24h"` for the default, or `f"{since}..{until}"`).
- `since`/`until` → optional ISO-8601 query params; default `until = clock.now()`,
  `since = until - 24h`. `computed_at = clock.now()`.

### Phase A — `api/v1/availability/` five-file feature (TDD)
- [ ] **A1** `models.py`: `AvailabilityDTO` mirroring `AvailabilityResult`'s fields (DTO, NOT the
      domain result type). `validation.py` (stdlib-only): `signal_key` required (non-empty);
      `interval_seconds` (if present) a positive int; `since`/`until` parseable — raise a structured
      error → 422 before any core call. Failing TestClient test
      (`backend/tests/test_availability_endpoint.py`): `GET /api/v1/availability?signal_key=X` with
      seeded fake observations → 200 + DTO; **no-data window** (no observations) → 200 with
      `availability_pct=None`/`completeness_pct=None` (NOT 500); missing `signal_key` → 422.
- [ ] **A2** `service.py`: thin — build the window (defaults via the injected clock), call
      `AvailabilityCalculator(observation_repo).compute(signal_key, since=.., until=.., interval=..,
      window=.., maintenance=lambda _:_False, computed_at=clock.now())`, map → `AvailabilityDTO`;
      DI provider `get_availability_service` (uses `get_observation_repo` + `get_clock` from
      `src.api.dependencies`). `controller.py`: `GET /availability`. Wire `observation_repo` into
      `create_app` (+ `app.state.observation_repo`, default `PostgresObservationRepository(engine)`)
      and add `get_observation_repo(request)` + `get_clock(request)` to `dependencies.py` if not
      present; register the router. Green. Commit. Docstrings cite §11/§13 (+ the maintenance stopgap).

### Phase B — `api/v1/history/` five-file feature (TDD)
- [ ] **B1** `models.py`: `ObservationDTO` (`signal_key`, `observed_at`, `health`, `location`,
      `latency_ms`; omit `source`/`raw_ref`/`source_event_id` from the client view — DTO, not the
      domain type). `validation.py`: `signal_key` required; `since`/`until` parseable. Failing
      TestClient test (`backend/tests/test_history_endpoint.py`): `GET /api/v1/history?signal_key=X`
      → 200 + observation DTOs (recent first); **empty** window → 200 + `[]`; missing `signal_key` → 422.
- [ ] **B2** `service.py`: thin — default the window via the clock, `observation_repo.in_window(...)`,
      map → `ObservationDTO`s (sorted most-recent first); DI provider `get_history_service`.
      `controller.py`: `GET /history`. Register the router. Green. Commit.

### Phase C — contract + shape tests + blast radius
- [ ] **C1** Add `"src.api.v1.availability"` + `"src.api.v1.history"` to the
      `api-feature-independence` `modules` list in `pyproject.toml`; `lint-imports` → **5 kept / 0 broken**.
- [ ] **C2** Five-file-shape test for EACH feature (working-agreements.md 2026-06-28) — assert the
      exact `{__init__, controller, models, validation, service}.py` set (mirror
      `test_components_endpoint.py::test_components_module_five_file_shape`).
- [ ] **C3** Wiki blast radius: `api-five-file-convention.md` (add `availability`+`history` features)
      + `architecture-boundary.md` (independence module list) updated + `verified_sha` bumped
      (symbol citations). If `create_app` gained `observation_repo`, that file is in
      `api-five-file-convention.md`'s `code_refs` → re-verify.
- [ ] **C4** Full SIX-command gate green.

**AC mapping:** AC1 ← A; AC2 ← B; AC3 ← A2/B2 window defaulting (test an explicit since/until too);
AC4 ← C1+C2; AC5 ← C3+C4.

---

## STORY-039 — Isolate DB-gated tests (2 pts, gate-only) — DO SECOND

- [ ] **039.1** Make DB-gated tests pass against a REUSED, already-populated DB. Audit all DB-gated
      tests in `backend/tests/test_persistence_adapters.py` (and any other DB-gated modules) for the
      "empty table" / "exactly N rows" assumption that breaks on a reused DB (the observed failures:
      `test_rejected_observation_save_*`). Fix via the lowest-friction approach that covers ALL
      DB-gated tests — PREFER a fixture-level change in `backend/tests/conftest.py` (a per-test
      transactional rollback, or truncate-between-tests) over editing each test; or scope each
      assertion to the rows it created. No production `src/` change.
- [ ] **039.2** Prove it: run the full suite TWICE in a row against the same container without
      teardown — both green. (`scripts/dev_db.py up`; `pytest`; `pytest` again; do NOT `down` between.)
      Record the two-run evidence in the story History.
- [ ] **039.3** Full SIX-command gate green.

**AC mapping:** AC1 ← 039.2; AC2 ← 039.1 (no global-count assumptions); AC3 ← 039.3.

---

## Standing conventions checklist (binds all new code)
- [ ] Docstrings cite the dossier §; DTOs distinct from domain types; DI provider in the feature
      `service.py`; controller imports only its models+service.
- [ ] Edge DTO maps ids/values directly — NO sentinel/`else 0` fallback (working-agreements.md 2026-06-28).
- [ ] Five-file-shape test per new feature (2026-06-28).
- [ ] Empty / no-data behavior tested (no observations → `None` pcts / `[]`); pure reads → TOCTOU N/A.
- [ ] Production `src/` never imports `tests` (contract-enforced). Scoped staging; mirror the
      components/maintenance feature structure.

## Notes / risks
- The per-signal availability endpoint carries two documented stopgaps (caller-supplied `interval`
  default 60s; no-maintenance) until STORY-040's config/topology lands — state them in the service
  docstring, do not silently hardcode without comment.
- No tooling/MCP change. No migration.
