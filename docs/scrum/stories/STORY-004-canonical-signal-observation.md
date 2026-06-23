---
id: STORY-004
title: Canonical SignalObservation type
type: feature
---

## Context
Spec: dossier §5 (Canonical signal) + §6 (vocabulary rule P3). Zone 1. The spine of
the whole system — the vendor-neutral form of one synthetic monitor execution from one
location. Vendor identifiers live ONLY in provenance.

## Description
Define the frozen, validated `SignalObservation` canonical type in `core/domain/`:
`signal_key` (stable name you choose, never a vendor id), `observed_at` (UTC),
`health` (closed enum: `up` / `down` / `degraded`), `source_event_id` (idempotency
key), `source` provenance `{system, native_id, native_kind}`, `location`, optional
`latency_ms`, optional `raw_ref`. Every field must make sense to a reader who has never
heard of Dynatrace.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: The type constructs and validates per §5; `health` is a closed enum
      (up/down/degraded); `observed_at` is UTC; the type is frozen/immutable.
- [ ] AC2: The vendor identifier appears ONLY inside the `source` provenance object,
      nowhere else on the type.
- [ ] AC3: Round-trip (construct → serialize → reconstruct) tests pass using in-memory
      canonical fixtures; invalid inputs are rejected.
- [ ] AC4: `lint-imports` confirms `core/domain` imports nothing outward (no vendor type).

## Open Questions
- Confirm estimate (seed: ~3) and the exact validation/serialization library at refinement
  (pydantic frozen model vs frozen dataclass).

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §5/§6. Status: draft — refine before its sprint.
