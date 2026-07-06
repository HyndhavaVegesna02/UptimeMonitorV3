---
id: STORY-053
title: Sock Shop on Railway + toggleable failure shim + demo cadence tuning
type: feature
---

## Context
Split out of STORY-017 at sprint-35 refinement (2026-07-06, PO-approved): the deployment
story ships without the demo-app tail because the Dynatrace monitor already has a live
target producing real results. This story completes the dossier §17 demo picture: the
REPLACEABLE monitored application under our control, with an on-demand failure mode that
is more realistic than sample-mode's forced-DOWN override (it fails the actual monitored
route, exercising the vendor detection path too).

**PO clarification (2026-07-06, post-sprint-36):** a sample demo app is ALREADY deployed
on Railway with the Dynatrace monitor set up against it — it is the live target whose
metrics the system consumes today. So the "deploy an app + point a monitor at it" half of
this story is ALREADY DONE outside the sprint flow; what remains is the failure shim and
the demo cadence tuning against that existing app. And landing this story does NOT
trigger sample-mode removal — sample mode stays.

## Description
A toggleable failure shim in front of ONE monitored route of the EXISTING Railway demo
app (returns 5xx/timeouts while ON, byte-identical while OFF); demo cadence tuned
(~1-min monitor frequency, short pull-loop poll interval via config).

## Acceptance Criteria (draft — refine before scheduling)
- [ ] AC1 (pre-satisfied, verify only): the existing demo app is reachable on its Railway
      URL and the existing Dynatrace HTTP monitor runs against it — confirmed, not built,
      by this story.
- [ ] AC2: The failure shim toggles via a simple authenticated mechanism; while ON the
      monitored route fails observably in Dynatrace; while OFF behavior is byte-identical.
- [ ] AC3: `config/apps` carries the app/signal with a tuned `interval_seconds`; the
      deployed worker picks it up without code change.
- [ ] ~~AC4~~ RESOLVED (PO, 2026-07-06): landing this does NOT trigger sample-mode
      removal; sample mode stays a separate, still-TEMPORARY feature (removal recipe
      remains in `docs/scrum/wiki/sample-mode.md` for whenever the PO calls it).

## Open Questions
- ~~Full Sock Shop vs a minimal demo app~~ MOOT (PO, 2026-07-06): the demo app already
  exists on Railway; nothing new gets deployed app-wise.
- ~~Does landing this trigger the sample-mode removal story?~~ RESOLVED: no (PO,
  2026-07-06).
- Shim mechanism: do we control the existing demo app's source/deployment (shim lands in
  its codebase or as a proxy service in front of it)? What is the app, and where does its
  code live? Decides the shim's shape and the estimate — confirm at refinement.

## History
- 2026-07-06: filed as draft at sprint-35 planning (split from STORY-017).
- 2026-07-06 (post-sprint-36): PO clarified — demo app + Dynatrace monitor already live
  on Railway (it is today's metrics source); no sample-mode-removal linkage. Scope shrinks
  to shim + cadence; likely re-estimate 3 → 2 once the shim-mechanism question is answered.
