---
id: STORY-011
title: Availability calculator
type: feature
---

## Context
Spec: dossier §11 (availability engine) + T2.5. Zone 4. The system's first calculator —
compute-only, no tables, part of the constant core. Runs parallel to the pipeline, never
consults the streak (P4). Derive-on-read, persists nothing (D-1).

## Description
`core/services/availability.py`: two-grain math. **Availability %** over collapsed
verdicts (`passing ÷ (total − maintenance)`, gaps excluded). **Completeness %** over raw
observations with a location-aware denominator (`actual ÷ (intervals × distinct_locations)`,
`intervals = window ÷ interval`, locations = `COUNT(DISTINCT location)`). Group rollup =
min of children (counts sum, percentages take min). Surface the skew flag. Shape the
entry points so a short-TTL cache could drop in later — but build NO cache.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Both metrics correct on in-memory fixtures (per §11 formulas).
- [ ] AC2: A 3-location signal never exceeds 100% completeness (location-aware denominator).
- [ ] AC3: A group's availability/completeness = min of its children; children with no
      data are excluded from the min but their absence stays visible.
- [ ] AC4: Derive-on-read — nothing persisted; entry points shaped for a drop-in cache,
      but no cache built (per working agreement: measure first).
- [ ] AC5: All SQL behind the repository port; service stays pure; `lint-imports` green.

## Open Questions
- Confirm gap policy default (`exclude`) and `AvailabilityResult` fields at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §11. Status: draft — refine before its sprint.
