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
- 2026-07-13: probed at Sprint 45 planning (not scheduled; stays DRAFT — deferred to a later sprint).
  Findings: `ComponentDTO` has no `group` (`api/v1/components/models.py:9-16`); `config/apps/*.yaml`
  is flat (no grouping) and `ComponentConfig` has no group field (`composition/config.py:57-73`) —
  grouping is a NEW config field + loader change + DTO + frontend sections. Uptime buckets are
  additive-only: `bucket_into_cycles()` already exists and is reusable
  (`core/queries/availability.py:133-165`), so a new derive-on-read `BucketedUptimeCalculator` fits
  in `core/queries/` (STORY-078's home) as a sibling — no persisted verdicts. Frontend Dashboard is
  one flat table today (`pages/DashboardPage.tsx:244-361`); `UptimeBar` is a generic N-segment
  renderer (`components/UptimeBar/UptimeBar.tsx`). Likely estimate **5** (grouping + buckets).
  Recommended-but-not-yet-PO-approved resolution for next refinement: `group` as an optional
  per-component `ComponentConfig` field (ungrouped → default section); buckets share the
  availability window (24h default) sliced into ~30 buckets.
