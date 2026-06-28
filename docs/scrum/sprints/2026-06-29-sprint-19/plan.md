# Sprint 19 — Plan

**Goal:** Publications feature module — a `PublicationRepository` over the EXISTING `publications`
table, a `RecordingPublisher` decorator that records each successful publish, and
`GET /api/v1/publications`. The last pure-backend feature before the credential-gated live demo.

**Branch:** `sprint-19` · **Start tag:** `sprint-19-start` · **Baseline:** `e95bc6b` (refinement on
branch; from main `1d53f39`).

**Committed: 5 pts** — STORY-037 (single-story sprint).

---

## How this sprint runs
The orchestrator finishes STORY-037 in-sprint via a **Sonnet** implementer subagent (PO request), then
runs the full six-command gate, the Opus reviewers, the wiki sweep, and review→verdict→merge→retro.
**TDD + commit-after-green. Scoped staging. Do NOT write `.scrum/` board state.**

### The six-command DoD gate — exit 0 each
`pytest` · `lint-imports` (**5 kept / 0 broken** — RecordingPublisher is composition; the publications
feature joins the EXISTING `api-feature-independence` contract; NO new contract) ·
`python scripts/check_fk_direction.py` · `alembic upgrade head` · `ruff check .` · `ruff format --check .`.
DB-gated: `scripts/dev_db.py up` → run → `down`. **No new migration** (the publications table exists).

### Established facts the implementer builds on
- `publications` table (spine schema, EXISTS): `id BIGSERIAL PK`, `component_id TEXT FK→components
  (RESTRICT)`, `proposal_id BIGINT FK→status_proposals (nullable, CASCADE)`, `status TEXT` (CHECK in
  `operational|degraded|partial_outage|major_outage`), `published_at TIMESTAMPTZ`. NO error column.
- `StatusChange` (`core/domain/status.py`): `{component_id: str, status: ComponentStatus}`.
  `StatusPublisherPort.publish(change) -> None` (`core/ports/status_publisher.py`). `ClockPort.now()`.
- Existing publisher composition: `composition/publish_helper.py::BestEffortPublisher` +
  `publish_best_effort`. New `RecordingPublisher` joins this module.
- Feature pattern + wiring: mirror `api/v1/components` + `api/v1/maintenance` (controller imports only
  its models+service; DI provider in the feature `service.py`; register router in `api/v1/__init__.py`;
  add `get_publication_repo` to `api/dependencies.py`; add a `publication_repo` param + `app.state`
  entry in `composition/app.py::create_app`). Frozen+validator pattern: `core/domain/maintenance.py`.
- Fakes (`backend/tests/fakes.py`): `FakeClock`, `RecordingStatusPublisher`, the repo fakes. DB-gated
  tests use the `migrated_db`/`engine` fixtures; `conftest.py::clean_topology` truncates topology tables
  — extend cleanup to `publications` (it FKs into components; truncate it in the tests that write it).

---

## STORY-037 — Publications feature module (5 pts) — gate + Opus reviewers

No migration. No new lint contract. The endpoint is a pure read (TOCTOU N/A); `record` is a plain INSERT.

### Phase A — `Publication` domain type (TDD)
- [ ] **A1** `backend/src/core/domain/publication.py::Publication` — frozen pydantic:
      `component_id: str`, `status: ComponentStatus`, `published_at: datetime` (UTC-validated, mirror
      `maintenance.py`), `proposal_id: int | None = None`, `id: int | None = None`. Export from
      `core/domain/__init__.py`. Docstrings cite §9/§12/§17. Test: valid constructs; naive `published_at`
      rejected.

### Phase B — `PublicationRepository` port + adapter + fake (TDD)
- [ ] **B1** Failing test (`test_core_ports.py`): `FakePublicationRepository.record(pub)` returns the
      window with an `id`; `list_recent()` returns most-recent-first; `[]` when empty.
- [ ] **B2** `core/ports/publication_repository.py::PublicationRepository` (abstract `record(publication)
      -> Publication`, `list_recent(limit: int = 50) -> list[Publication]`); export from
      `core/ports/__init__.py`; implement `FakePublicationRepository`. Green.
- [ ] **B3** Failing DB-gated test (`test_persistence_adapters.py`): `PostgresPublicationRepository`
      `record` INSERTs + returns the row with `id`; `list_recent` SELECTs ordered by `published_at`
      DESC (limit), `[]` when empty. Fake/adapter parity. Clean the `publications` table in the test.
- [ ] **B4** `adapters/persistence/publication_repository.py::PostgresPublicationRepository(engine)`.
      Green.

### Phase C — `RecordingPublisher` decorator (TDD)
- [ ] **C1** Failing test (`test_publish_helper.py` or similar, fakes only):
      `RecordingPublisher(delegate, repo, clock).publish(change)` calls `delegate.publish` then records
      a `Publication(component_id=change.component_id, status=change.status, published_at=clock.now())`;
      a RAISING delegate → nothing recorded + the error propagates; and
      `BestEffortPublisher(RecordingPublisher(raising_delegate, repo, clock))` logs+swallows and records
      nothing.
- [ ] **C2** `composition/publish_helper.py::RecordingPublisher(StatusPublisherPort)` — `__init__(self,
      delegate, publication_repo, clock)`; `publish`: `delegate.publish(change)` then
      `publication_repo.record(...)`. Docstring: records SUCCESSES only (the table has no error column);
      composes inside `BestEffortPublisher` (assembled live in STORY-016). Green.

### Phase D — `api/v1/publications/` five-file read feature + wiring (TDD)
- [ ] **D1** `models.py`: `PublicationDTO {component_id, status, published_at, proposal_id, id}` (DTO,
      not the domain type). `validation.py` (stdlib-only; no input for this GET). Failing TestClient test
      (`test_publications_endpoint.py`): `GET /api/v1/publications` → 200 + list most-recent-first; empty
      → 200 + `[]`.
- [ ] **D2** `service.py` (thin: resolve `PublicationRepository` via the container → `list_recent` →
      DTOs; DI provider `get_publications_service` using a new `get_publication_repo` in
      `api/dependencies.py`). `controller.py`: `GET /publications`. Wire `publication_repo` into
      `create_app` (+ `app.state`, default `PostgresPublicationRepository(engine)`); register the router.
      Five-file-shape test. Green.
- [ ] **D3** Add `"src.api.v1.publications"` to the `api-feature-independence` `modules` list in
      `pyproject.toml`; `lint-imports` → 5 kept / 0 broken.

### Phase E — blast radius + gate
- [ ] **E1** Wiki blast radius via the MECHANICAL sweep (2026-06-28): update/re-verify EVERY stale
      article — expect canonical-types-and-ports (Publication + PublicationRepository),
      persistence-adapters (the adapter), statuspage-publish (RecordingPublisher),
      api-five-file-convention (the feature). Symbol citations; bump verified_sha.
- [ ] **E2** Full SIX-command gate green (DB up). Leave the DB container running for review.

**AC mapping:** AC1 ← B; AC2 ← C; AC3 ← D; AC4 ← E.

---

## Standing conventions checklist (binds all new code)
- [ ] Docstrings cite the dossier §; `Publication.published_at` UTC-validated (frozen-type invariant 2026-06-26).
- [ ] Empty/edge tested (`list_recent` → `[]`); fake/adapter parity (2026-06-26); DTO distinct from domain.
- [ ] DI provider in the feature `service.py`; controller imports only its models+service.
- [ ] DB-gated tests stay green on a REUSED DB — clean the `publications` table the tests write.
- [ ] `src` never imports `tests`; no sentinel mappings; scoped staging; mirror existing patterns.
- [ ] Wiki blast radius = the mechanical sweep over ALL articles.

## Notes / risks
- Mirrors STORY-036 (maintenance) closely — a known-good 5. The one new shape is the `RecordingPublisher`
  decorator (composes with `BestEffortPublisher`; live chain assembly is STORY-016).
- No migration, no new tooling/contract.
