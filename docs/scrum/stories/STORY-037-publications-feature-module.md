---
id: STORY-037
title: Publications feature module — record publish history + the Publications tab
type: feature
---

## Context
Spec: dossier §9 (modularity — a stateful feature module owning inward-FK'd tables) + §12/T1.1
(commit-first, best-effort publish) + §17 (Publications tab). The last pure-backend feature before the
credential-gated live demo. The Statuspage publish adapter (STORY-013) publishes status changes but
nothing RECORDS the outcomes; the Publications tab has no backing. This adds the publications
repository, records each successful publish, and serves the Publications read endpoint.

## Refinement decisions (grounded in the schema + publish path, 2026-06-29)
- **The `publications` table ALREADY EXISTS** (spine schema, STORY-006): `id BIGSERIAL PK`,
  `component_id TEXT FK→components`, `proposal_id BIGINT FK→status_proposals (nullable, CASCADE)`,
  `status TEXT` (CHECK in the four ComponentStatus values), `published_at TIMESTAMPTZ`. **No migration.**
- **Record SUCCESSFUL publishes only.** The table has NO error/outcome column — it holds *what was
  published*, not failed attempts. So a publication row is written only after a publish SUCCEEDS;
  a failed publish is logged best-effort (BestEffortPublisher) and not recorded. (Resolves the draft's
  "record failures?" question — the schema constrains it to successes; recording failures would need a
  schema change, out of scope.)
- **Recording is wired via a `RecordingPublisher` decorator** (composition), NOT in core and NOT in the
  Statuspage adapter — keeps core pure and the adapter provider-focused. It composes with
  `BestEffortPublisher`: the production chain (assembled in the live-wiring story STORY-016) is
  `BestEffortPublisher(RecordingPublisher(StatuspagePublisher))` — record on success; if the real
  publish raises, RecordingPublisher does not record and re-raises; BestEffortPublisher logs+swallows.

## Description
1. **Core:** `core/domain/publication.py::Publication` (frozen read model: `component_id:str`,
   `status:ComponentStatus`, `published_at:datetime` (UTC-validated, mirror peers),
   `proposal_id:int|None=None`, `id:int|None=None`). `core/ports/publication_repository.py::
   PublicationRepository` with `record(publication) -> Publication` (INSERT; returns persisted with id)
   and `list_recent(limit: int = 50) -> list[Publication]` (most-recent-first; `[]` when none).
2. **Adapters:** `PostgresPublicationRepository` (against the existing table) + `FakePublicationRepository`
   (tests/fakes.py); fake/adapter parity (empty → `[]`; record returns id; list ordered by
   `published_at` desc).
3. **Composition:** `composition/publish_helper.py::RecordingPublisher(StatusPublisherPort)` — wraps a
   delegate + a `PublicationRepository` + a `ClockPort`: `publish(change)` calls `delegate.publish`,
   then on success `repo.record(Publication(component_id=change.component_id, status=change.status,
   published_at=clock.now()))`. A delegate failure propagates BEFORE recording (nothing recorded).
4. **API:** `api/v1/publications/` five-file read feature — `GET /api/v1/publications` → list of
   `PublicationDTO` (most-recent-first). Add `src.api.v1.publications` to the `api-feature-independence`
   contract module list. Wire `publication_repo` into `create_app`/`app.state` + a `get_publication_repo`
   dependency (mirror components/maintenance).

## Acceptance Criteria (refined — PO-approved 2026-06-29)
- [ ] AC1 (repository + parity): `PublicationRepository` (`record`, `list_recent`) with Postgres adapter
      + fake; DB-gated test; fake and adapter AGREE on: empty → `[]`, `record` returns a persisted row
      with `id`, `list_recent` ordered most-recent-first. (No migration.)
- [ ] AC2 (RecordingPublisher): on a SUCCESSFUL delegate publish, a `Publication` is recorded
      (component_id, status, published_at from the clock); if the delegate RAISES, nothing is recorded
      and the error propagates (tested with a fake delegate + fake repo + fake clock). Composes with
      `BestEffortPublisher` (a test shows `BestEffortPublisher(RecordingPublisher(raising))` logs+swallows
      and records nothing).
- [ ] AC3 (GET endpoint): `GET /api/v1/publications` → 200 with recorded publications as DTOs
      (most-recent-first; DTO distinct from the domain type); empty → 200 + `[]`. Five-file shape +
      shape test; `lint-imports` 5/0 with `publications` added to `api-feature-independence`.
- [ ] AC4 (full SIX-command DoD gate green); forward blast radius (MECHANICAL sweep):
      canonical-types-and-ports (Publication + PublicationRepository), persistence-adapters (the
      adapter), statuspage-publish (RecordingPublisher), api-five-file-convention (the feature) updated
      + re-verified.

## Conventions checklist
- Docstrings cite §9/§12/§17; `Publication.published_at` UTC-validated; empty/edge tested; fake/adapter
  parity (2026-06-26); DTO distinct from domain; DI provider in the feature `service.py`; no sentinel
  mappings (2026-06-28); `src` ⊥ `tests`; DB-gated tests clean the `publications` table they write (so
  the reused-DB suite stays green — extend the STORY-039/clean_topology pattern).
- Pure reads on the endpoint (TOCTOU N/A). `record` is a plain INSERT (not check-then-act).
- The live publisher chain (`BestEffortPublisher(RecordingPublisher(StatuspagePublisher))`) is
  ASSEMBLED in STORY-016 (live wiring) — this story provides + unit-tests `RecordingPublisher`; it does
  not wire a live composition root.

## Resolved Questions
- **Record successes only** (schema has no error column). **Decorator-based wiring** (composition),
  composes with BestEffortPublisher. **No migration** (table exists). (2026-06-29.)

## History
- 2026-06-28: created from Sprint 13 planning (Publications tab had no backing state).
- 2026-06-29 (Sprint 19 refinement): table exists (no migration); record successes only;
  RecordingPublisher decorator; GET endpoint. Estimate **5** (domain type + repo port/adapter/fake +
  decorator + five-file read feature + tests). Status: draft → ready.
