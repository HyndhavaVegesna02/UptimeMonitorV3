---
id: STORY-010
title: Four-stage core pipeline
type: feature
---

## Context
Spec: dossier §10 (core logic pipeline). Zone 4. The constant core's brain, expressed
as four pure, provider-blind stages. Nothing here mentions Dynatrace/DQL.

## Description
In `core/services/`: `collapse` (locations → one verdict per cycle; maintenance excluded
and short-circuits the rest) → `streak` (consecutive same-health verdicts over
non-maintenance verdicts only) → `anti-flap` (streak length → proposed status, per-app
config thresholds, resolved component → app → block) → `decide` (proposed vs current →
degradation proposal / auto-publish recovery / nothing; reconciles open proposals;
computes skew flag). All pure, unit-tested with in-memory canonical fixtures.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Each stage is unit-tested with canonical fixtures per §10.
- [ ] AC2: Maintenance is excluded from the verdict and from the streak; a maintenance
      cycle short-circuits the pipeline.
- [ ] AC3: Direction is severity-ordered: worse → proposal (human gate), better →
      recovery (auto-publish), same → nothing.
- [ ] AC4: Pure and provider-blind — no vendor/HTTP/SQL imports; `lint-imports` green;
      tests need no live services.

## Open Questions
- Confirm the per-app config resolution mechanics and default thresholds at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §10. Status: draft — refine before its sprint.
