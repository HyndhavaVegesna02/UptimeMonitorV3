---
id: STORY-067
title: Component grouping + per-component uptime-bucket API
type: feature
---

## Context
Filed 2026-07-07 from the Sprint 38 redesign data-gap analysis. The mock's Dashboard groups
components into named sections (with a worst-status header per group) and draws a per-component
uptime sparkline of ~30 time buckets. `ComponentDTO` has no `group`, and there is no per-component
uptime-bucket endpoint. STORY-057 renders a single group and omits/derives the sparkline from
availability/history where possible; this story adds the real grouping + bucket data.

## Description (to refine)
Add a component `group`/topology grouping (config-driven, per `config/apps`) surfaced on the
read model, and a per-component bucketed-uptime endpoint (N buckets over a window) so the Dashboard
sparkline reflects real historical status rather than being derived/omitted. Then the frontend
renders grouped sections + the real `UptimeBar`.

## Acceptance Criteria (to refine)
- [ ] Add grouping to the component read model (source it from `config/apps`); DTO + tests.
- [ ] Add a bucketed-uptime read endpoint (derive-on-read; no persisted verdicts per the WA); tests.
- [ ] Frontend: grouped Dashboard sections + `UptimeBar` bound to real buckets.

## Open Questions
- Bucket granularity/window defaults? Group taxonomy — from `config/apps` topology or a new field?

## History
- 2026-07-07: filed from the redesign data-gap analysis. Status: draft (needs refinement + estimate).
