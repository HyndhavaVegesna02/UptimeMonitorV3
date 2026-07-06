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

## Description
Sock Shop (or an equivalently simple demo app) deployed as a second Railway service; a
toggleable failure shim in front of ONE monitored route (returns 5xx/timeouts while ON);
the Dynatrace monitor repointed/added against it; demo cadence tuned (~1-min monitor
frequency, short pull-loop poll interval via config).

## Acceptance Criteria (draft — refine before scheduling)
- [ ] AC1: Sock Shop reachable on a Railway URL; a Dynatrace HTTP monitor runs against it
      from ≥2 locations.
- [ ] AC2: The failure shim toggles via a simple authenticated mechanism; while ON the
      monitored route fails observably in Dynatrace; while OFF behavior is byte-identical.
- [ ] AC3: `config/apps` gains the new app/signal with a tuned `interval_seconds`; the
      deployed worker picks it up without code change.
- [ ] AC4: relationship to sample mode decided at refinement (the PO's TEMPORARY
      sample-mode feature may be REMOVED once this lands — its removal recipe is in
      `docs/scrum/wiki/sample-mode.md`).

## Open Questions
- Full Sock Shop (microservices, heavy) vs a minimal echo/demo app — Railway free-tier
  footprint decides; confirm at refinement.
- Does landing this trigger the sample-mode removal story?

## History
- 2026-07-06: filed as draft at sprint-35 planning (split from STORY-017).
