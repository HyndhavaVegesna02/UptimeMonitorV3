---
id: STORY-072
title: Publication outcome — record every approve publish attempt (succeeded/failed) independent of Statuspage publish
type: feature
---

## Context
Found live during the Sprint 39 wrap (2026-07-08): approving a real proposal succeeded
(`POST /decisions/2 → 200`) but nothing appeared in the Publications tab. Root cause (systematic
debugging): the publisher chain is `StatusWritebackPublisher(BestEffortPublisher(RecordingPublisher(real)))`,
and `RecordingPublisher` records **only SUCCESSFUL** publishes (`publication_repository`: "Records
SUCCESSFUL Statuspage publishes only — the table has no error column"). The real Statuspage publish
failed with **401 "Could not authenticate"** (invalid/expired `STATUSPAGE_API_KEY`), so
`RecordingPublisher` never recorded, `BestEffortPublisher` swallowed the 401, and the tab stayed empty.

**PO decision (2026-07-08, via AskUserQuestion):** the publication record must be written on approve
**independent of** whether the Statuspage publish succeeds, and must carry a **success/failed
outcome**. The Statuspage publish stays best-effort (the 401 credential fix is deferred to the PO) —
so until the key is refreshed, approving records a publication with `outcome = failed`, which is
exactly the visible audit trail wanted.

This delivers the **outcome** portion of the deferred STORY-066 (author/incident remain in 066).

## Acceptance Criteria
- [ ] AC1: Every approve publish ATTEMPT records exactly one publication row, INDEPENDENT of Statuspage
      success — a successful publish → `outcome = 'succeeded'`; a raising delegate (e.g. 401) →
      `outcome = 'failed'`. Approve still returns 200 (publish stays best-effort/swallowed). DB-gated
      tests drive BOTH the success path and the failure (raising-delegate) path and assert a row is
      recorded with the correct outcome. Fake/adapter parity preserved.
- [ ] AC2: The `publications` table gains an `outcome` column via a real Alembic migration (up +
      down clean). If a CHECK constraint is used, its allowed values are consistent (e.g.
      `('succeeded','failed')`) AND a DB-gated test writes each allowed value AND proves a
      disallowed value is rejected — applying the Sprint 39 retro lesson (STORY-071 class). No
      spine→feature FK (check_fk_direction stays 0 violations).
- [ ] AC3: `PublicationDTO` + `api/v1/publications` expose `outcome`; endpoint test covers it.
- [ ] AC4: The Publications timeline (frontend) renders the outcome as a chip (per the Operator
      Dashboard mock) — success vs failed styling, token-only colors, dot+text (never color-only);
      frontend test drives both outcomes via MSW.
- [ ] AC5: Backend six-gate DoD + frontend three-gate DoD green.

## Out of scope
- Fixing the Statuspage 401 credential (PO refreshes `STATUSPAGE_API_KEY`; entering secrets is not
  something the dev team does). Publish remains best-effort.
- Publication `author` / `incident` metadata (stays in STORY-066).

## Open Questions
None — design decided by the PO at intake.

## History
- 2026-07-08: found live + root-caused (systematic debugging); PO chose record-with-outcome +
  defer-publish. Status: ready. Scheduled to sprint-40.
