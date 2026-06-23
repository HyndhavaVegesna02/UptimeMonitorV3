---
id: STORY-008
title: Dynatrace adapter + DQL normalization
type: feature
---

## Context
Spec: dossier §5 (normalization rules) + §7 (mapping) + §8 (ingest). Zone 3. Vendor
specifics fully contained in the adapter; the core stays untouched.

## Description
In `adapters/inbound/dynatrace/`: query synthetic monitor results via DQL and normalize
each location execution into a canonical `SignalObservation`. Per-monitor-type
normalizers (HTTP, clickpath, single-browser, NAM) all flatten to the SAME canonical
shape; the type survives only as `native_kind`. The adapter is dumb and lossless — it
does NOT aggregate (collapse is a core step).

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: Given recorded DQL responses (fixtures), the adapter produces the correct
      canonical `SignalObservation`s.
- [ ] AC2: The adapter lives entirely in `adapters/`; `lint-imports` confirms the core
      is untouched and no adapter imports another adapter.
- [ ] AC3: Each monitor type's normalizer flattens to the same canonical shape; the
      vendor type appears only as `native_kind` in provenance.
- [ ] AC4: No live Dynatrace required — tests run against recorded fixtures.

## Open Questions
- Confirm which monitor types are in scope for the demo vs deferred.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §5/§7/§8. Status: draft — refine before its sprint.
