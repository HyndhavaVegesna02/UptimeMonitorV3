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
Make the history endpoint honor its `limit` parameter (or remove the parameter if it was
never intended — decide at refinement against the API contract in
`backend/src/api/v1/history/`).

## Acceptance Criteria (draft — refine at planning)
- [ ] AC1: given `limit=N`, the endpoint returns at most N observations (newest first),
      verified by a test hitting the real repository path.
- [ ] AC2: absent `limit`, current behavior is preserved (documented default).
- [ ] AC3: the frontend Check History tab's usage is audited against the fix (it may rely
      on the current ignore-limit behavior via its own render cap).

## Open Questions
- Is `limit` silently unwired in the API layer, the repository query, or both?

## History
- 2026-07-17: filed at sprint-50 review (PO: accept STORY-089 + follow-up). Needs
  refinement + estimate.
