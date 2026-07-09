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

**PO decision (2026-07-06, sprint-37 refinement — shim mechanism):** we do NOT control
the existing demo app's source. The failure shim is therefore a SEPARATE small proxy
service deployed on Railway, sitting in front of the monitored route; the Dynatrace
monitor is repointed at the proxy URL. While the shim is ON the proxy returns 5xx/timeouts
for the monitored route; while OFF it passes through byte-identically to the real app.

**Console/deploy dependency — NOT console-free.** Building the proxy is hermetic code, but
AC1/AC2 are inherently live (Railway deploy of the proxy + Dynatrace repoint + observing
the failure in Grail). Per the 2026-06-29 live-verification agreement those ACs run
before close or split out — so this story carries the same PO-console dependency as
STORY-017 and belongs with the deploy work (schedule alongside/after 017's live tail),
NOT in a console-free sprint.

## Description
A small toggleable failure-shim PROXY service on Railway in front of ONE monitored route
of the existing demo app (returns 5xx/timeouts while ON; transparent pass-through while
OFF); the Dynatrace monitor repointed at the proxy; demo cadence tuned (~1-min monitor
frequency, short pull-loop poll interval via config).

## Acceptance Criteria (draft — refine before scheduling)
- [ ] AC1 (pre-satisfied, verify only): the existing demo app is reachable on its Railway
      URL and the existing Dynatrace HTTP monitor runs against it — confirmed, not built,
      by this story.
- [ ] AC2: the proxy shim toggles via a simple authenticated mechanism; while ON the
      monitored route fails observably in Dynatrace; while OFF the proxy is a transparent
      pass-through (byte-identical to the real app). Proxy logic unit-tested hermetically;
      the ON→observed-in-Grail path verified live.
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
- ~~Shim mechanism~~ RESOLVED (PO, 2026-07-06): separate proxy service (we don't control
  the app's source).
- Remaining before scheduling: authenticated-toggle mechanism detail (env flag vs a
  tiny control endpoint) and the exact monitored route the proxy fronts — small; settle
  when this is scheduled with the deploy work.

## History
- 2026-07-06: filed as draft at sprint-35 planning (split from STORY-017).
- 2026-07-06 (post-sprint-36): PO clarified — demo app + Dynatrace monitor already live
  on Railway (it is today's metrics source); no sample-mode-removal linkage. Scope shrinks
  to shim + cadence.
- 2026-07-06 (sprint-37 refinement): PO chose the proxy-service shim shape (we don't
  control the app's source). Estimate held at 3 (a deployed proxy service + repoint +
  live verify). Stays DRAFT and console-gated — belongs with STORY-017's deploy work, not
  a console-free sprint; kept out of sprint 37 for that reason.
- 2026-07-09: marked archived by Product Owner directive (not required).
