---
id: STORY-081
title: Publication incident-id capture (Statuspage response → Publications timeline)
type: feature
---

## Context
Split out of STORY-066 at Sprint 45 refinement (2026-07-13). The mock's Publications timeline shows
an incident reference alongside author + outcome. STORY-066 delivered author (derivable); STORY-072
delivered outcome. The **incident id** is the remaining, genuinely-new-and-speculative piece.

Scout probe (2026-07-13) findings:
- The Statuspage response is **discarded at the executor boundary**: `StatuspagePublisher.publish`
  calls the http executor but ignores its return (`adapters/outbound/statuspage/__init__.py:39-56`);
  `http_executor.py:27-53` returns `resp.json()` but nobody receives it. `RecordingPublisher`
  receives no response from the delegate (`composition/publish_helper.py:100-127`), and the
  publications table has no incident column.
- The current publish flow **only PATCHes component status** — it does not create Statuspage
  incidents at all. So "incident id" may not exist in the current flow; capturing it likely
  requires deciding whether we adopt Statuspage incident creation, not just plumbing a response id.

## Description (to refine)
Capture a Statuspage identifier on the publication record + `PublicationDTO` and render it in the
timeline. Requires: publisher returns the Statuspage response; `RecordingPublisher` captures it; a
new nullable `incident_id` (or `statuspage_ref`) column + migration; domain/DTO threading; frontend.

## Open Questions (for refinement)
- Is Statuspage **incident creation** in scope, or only the component-status-update response id?
- What identifier does the component-status PATCH response actually return (needs a live probe /
  Statuspage API sample)? Requires working Statuspage credentials (currently 401-deferred).

## History
- 2026-07-13: filed as the incident split-out of STORY-066 at Sprint 45 refinement. Status: draft
  (needs refinement + estimate; blocked on a Statuspage design decision + live response sample).
