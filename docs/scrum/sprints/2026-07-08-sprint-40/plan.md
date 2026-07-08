# Sprint 40 — Publication outcome, recorded independent of publish (STORY-072)

**Goal:** Approve must record a Publications entry regardless of whether the Statuspage publish
succeeds, carrying a `succeeded`/`failed` outcome. Publish stays best-effort (401 credential deferred
to the PO).

## Root cause (confirmed, systematic debugging)
Publisher chain `StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(real)))`.
`RecordingPublisher.publish` calls the delegate then records ONLY on success
(`composition/publish_helper.py`; `publication_repository.record` docstring: "Records SUCCESSFUL
Statuspage publishes only"). The real publish raised `StatuspageApiError` (401), so nothing recorded;
`BestEffortPublisher` swallowed it → approve returned 200 but Publications empty.

## The change (full-stack)
1. **Schema** — new Alembic migration: add `publications.outcome` (text). If CHECK-constrained, use
   `outcome IN ('succeeded','failed')` (consistent values) AND add a DB-gated test that writes each
   allowed value and proves a disallowed value is rejected (STORY-071 / Sprint-39 retro lesson —
   fakes can't model DB constraints). Up + down clean; no spine→feature FK.
2. **Record-always** — change the recording so it writes a publication row on BOTH the success and
   the failure paths with the right `outcome`. Cleanest: `RecordingPublisher` records `succeeded`
   after the delegate returns, and on a raising delegate records `failed` then RE-RAISES (so the
   outer `BestEffortPublisher` still swallows for the caller — approve stays 200). Keep the
   StatusWriteback + BestEffort ordering. Update `Publication` domain type + `publication_repository`
   (and the in-memory FAKE) to carry `outcome`; keep fake/adapter parity.
3. **API** — `PublicationDTO` + `api/v1/publications` (models/service) expose `outcome`; endpoint test.
4. **Frontend** — Publications timeline renders the outcome as a chip (per the Operator Dashboard
   mock's `{{ p.outcome }}`): `succeeded` vs `failed` styling, token-only colors, dot + text label
   (never color-only). MSW-drive both outcomes in a test.

## Verified contract notes
`Publication` domain (`core/domain`), `publication_repository.record`/`list_recent`,
`api/v1/publications/models.py::PublicationDTO`, `features/publications/*` + `PublicationsPage`
(Timeline). The frontend already renders the timeline (STORY-062); this adds the outcome chip it
omitted.

## Conventions checklist (held at review)
- Backend: five-file API shape for any api change; docstrings citing dossier §; frozen types enforce
  invariants; empty-input + edge tests; DB-gated tests use `migrated_db`; SINGLE pytest invocation
  reusing `DATABASE_URL` (55432; writers stopped) — no second DB.
- Frontend: token-only colors; a11y (dot+text, reduced-motion); tests by role/name; MSW only edge.
- Backend six-gate + frontend three-gate DoD. Commit per green step; scoped staging. Wiki sweep
  (statuspage-publish / publications / frontend-zone articles may have code_refs). Do NOT edit `.scrum/`.
- OUT OF SCOPE: the Statuspage 401 credential (PO refreshes `STATUSPAGE_API_KEY`); publish stays
  best-effort. Publication author/incident (STORY-066).
