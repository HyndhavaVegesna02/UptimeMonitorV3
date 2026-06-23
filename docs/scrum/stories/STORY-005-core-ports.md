---
id: STORY-005
title: The core ports
type: feature
---

## Context
Spec: dossier §6 (Ports & interfaces) + §8 (ingest contract). Zone 1. Ports are
interfaces the core OWNS but does not implement — the inversion that lets the core
depend on nothing.

## Description
Define in `core/ports/`, in canonical vocabulary only: `SignalIngestPort` (inbound —
batches, idempotent + validating by contract), `StatusPublisherPort` (outbound — sends
a canonical `StatusChange` with a canonical `component_id`), the repository ports
(`ObservationRepository`, `WatermarkRepository`, …), and `ClockPort` (injected `now()`).
A reader who has never heard of Dynatrace must understand every signature.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: All ports defined in `core/ports/` with signatures in canonical vocabulary
      only (no vendor/HTTP/SQL types in the interfaces).
- [ ] AC2: `lint-imports` confirms `core` imports no adapter and no vendor library.
- [ ] AC3: A fake/in-memory implementation of each port compiles against the interface
      and is usable in tests.
- [ ] AC4: `core/ports` may import `core/domain` but not `core/services` (layering
      contract green).

## Open Questions
- Confirm the full repository-port set and the `StatusChange` shape at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §6/§8. Status: draft — refine before its sprint.
