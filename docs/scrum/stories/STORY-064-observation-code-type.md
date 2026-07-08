---
id: STORY-064
title: Observation HTTP status code + check type on ObservationDTO
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Check History grid has
"Type" and HTTP "Code" columns. `ObservationDTO` (`api/v1/history/models.py`) is
`{signal_key, observed_at, health, location, latency_ms?}` — neither exists. STORY-060 omits both
columns; this story adds them.

## Description (to refine)
Surface the HTTP status code and the check/monitor type from the ingested Dynatrace observation
through the domain `SignalObservation` (if captured) → `ObservationDTO`. Verify against the real
Grail schema what is actually captured (per the dynatrace-grail memory) before promising fields.

## Acceptance Criteria (to refine)
- [ ] Confirm code/type are captured in ingest (or add capture); thread to `ObservationDTO`; tests.
- [ ] Frontend: add the Type + Code columns back to the Check History grid.

## Open Questions
- Are HTTP code + monitor type present in the current `http_monitor_execution` normalization?

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
