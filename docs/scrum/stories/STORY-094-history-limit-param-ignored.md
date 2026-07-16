---
id: STORY-094
title: Defect — /api/v1/history ignores its `limit` query param
type: defect
---

## Context
Found during the STORY-089 live verification (sprint-50 review, 2026-07-17):
`GET /api/v1/history?signal_key=http-check&limit=2` against the deployed stack returned
the full window of observations (~130 rows), not 2. Filed at review as the
accept-with-follow-up on STORY-089.

## Description
Add a real, optional `limit` query parameter to `GET /api/v1/history`: when supplied,
return at most N observations (newest-first, i.e. the cap applies AFTER the existing
most-recent-first sort); when absent, behavior is byte-identical to today (full window).

## Refinement finding (2026-07-17)
`limit` never existed: the controller declares only `signal_key`/`since`/`until`
(`backend/src/api/v1/history/controller.py:19-27`); FastAPI silently ignores unknown
query params (the review probe's `limit=2` was a no-op, not a bug). The frontend never
sends `limit` — `client.ts::getHistory` deliberately fetches the full window and the
Check History tab caps RENDERING client-side (`frontend/src/api/client.ts:210-217`,
STORY-015e AC4). Reframed from "defect" to "missing server-side cap": on the deployed
system a wide window ships thousands of rows over the wire for a 1000-row render.

## Acceptance Criteria
- [ ] AC1: `limit=N` (int ≥ 1) returns at most N observations, newest-first — the N most
      recent in the window — verified by a test against the real DynamoDB-Local
      repository path.
- [ ] AC2: absent `limit`, the response is unchanged (existing tests stay green
      untouched); `limit=0`/negative/non-int → clean 422 via the existing validation
      seam (`validation.py`), consistent with the maintenance-tab edge-422 convention
      (STORY-052).
- [ ] AC3: the client-side render-cap comments in `frontend/src/api/client.ts` and
      `CheckHistoryPage.tsx` are reconciled with the new param (docs-only; the frontend
      does NOT adopt `limit` in this story — its render cap stays authoritative).
- [ ] AC4: story-scoped DoD gate green.

## Open Questions
None (resolved at refinement — see finding above).

## History
- 2026-07-17: filed at sprint-50 review (PO: accept STORY-089 + follow-up). Needs
  refinement + estimate.
- 2026-07-17: refined — investigation showed the param never existed and the frontend
  never sends it; reframed as an additive optional cap. Estimate 2. PO directive
  "fix story 94" → approved for sprint 51.
