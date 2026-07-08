# Sprint 40 Review — Publication outcome, recorded independent of publish

**Outcome:** STORY-072 accepted (5/5 pts). Merged to `main`.

## STORY-072 — approve records a Publications entry with a success/failed outcome
- **Root cause:** `RecordingPublisher` recorded SUCCESSFUL publishes only; the real Statuspage publish
  failed 401 → nothing recorded → Publications empty (approve still 200 via best-effort).
- **Change (full-stack):** migration adds `publications.outcome` (`succeeded`/`failed`, CHECK-constrained,
  existing rows backfilled to `succeeded`); `RecordingPublisher` records on BOTH paths (success→succeeded,
  failing delegate→failed then re-raise so best-effort still swallows); `PublicationOutcome` enum;
  `PublicationDTO.outcome`; Publications timeline outcome chip (reuses `StatusBadge`).
- **Verified (orchestrator, fresh throwaway DB):** nine-gate DoD green — backend pytest **522 passed**,
  frontend **356 passed**, lint-imports 5/0, fk 11/0, alembic OK, ruff clean.
- **Tests:** DB-gated test drives the REAL RecordingPublisher+BestEffortPublisher+Postgres chain on both
  success and failing-publish paths (exactly one row each, correct outcome, caller sees no exception) +
  a CHECK allowed-and-rejected DB test (STORY-071 retro lesson applied). **Spec PASS / quality APPROVE (Opus).**
- **Provenance:** found live at the Sprint 39 wrap once real data flowed and a real proposal was approved.

## Deferred (PO decision)
- Statuspage publish stays best-effort; the 401 "Could not authenticate" credential
  (`STATUSPAGE_API_KEY`) is the PO's to refresh. Until then, approve records `outcome='failed'` — the
  visible audit trail requested.
- Publication author/incident metadata remains in STORY-066.

## Follow-ups
- MINOR: `publish_helper` failure path — if `record()` itself raises, it masks the original delegate
  error (best-effort still swallows; approve stays 200). Benign edge; optional follow-up.
