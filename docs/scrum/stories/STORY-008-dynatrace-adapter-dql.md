---
id: STORY-008
title: Dynatrace adapter + DQL normalization
type: feature
---

## Context
Spec: dossier §5 (canonical signal + normalization rules) + §6 (ports) + §7 (mapping) +
§8 (ingest). Zone 3, inbound adapter. Vendor specifics are fully contained in the
adapter; the core stays untouched (`lint-imports` proves it). The adapter is the
dependency root of Zone 3 — STORY-009's pull loop calls it.

## Description
In `backend/src/adapters/inbound/dynatrace/`: query synthetic monitor results via DQL
and normalize each **location execution** into a canonical `SignalObservation`
(`backend/src/core/domain/signal.py`). Per-monitor-type normalizers dispatch on the
vendor monitor type and all flatten to the SAME canonical shape; the type survives only
as `source.native_kind` in provenance. The adapter is deliberately dumb and lossless —
it does NOT aggregate (collapse to one verdict per cycle is a core step, dossier §10).

**Scope (refined 2026-06-25):** in scope = **HTTP** and **browser clickpath** synthetic
monitors (the Sock Shop demo: API/endpoint checks + a user-journey clickpath).
**single-browser and NAM are out of scope** for this story; the normalizer-dispatch seam
leaves them addable later without editing the existing normalizers.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: Given recorded DQL response fixtures for **HTTP** and **browser-clickpath**
      synthetic monitor executions, the adapter produces the correct canonical
      `SignalObservation` for each location execution — every field populated per §5
      (`signal_key`, `observed_at` as tz-aware UTC, `health`, `source_event_id`,
      `source = {system, native_id, native_kind}`, `location`, optional `latency_ms`,
      optional `raw_ref`). One observation **per location execution**; the adapter never
      aggregates.
- [ ] AC2: The adapter lives entirely under
      `backend/src/adapters/inbound/dynatrace/`; `lint-imports` stays green — the core is
      untouched and no adapter imports another adapter. No vendor type or vendor id
      crosses into core (vendor id appears only in `source`).
- [ ] AC3: HTTP and browser-clickpath each have their **own normalizer** that flattens to
      the same canonical shape; the vendor monitor type appears only as
      `source.native_kind`. A multi-step clickpath collapses to one monitor-level `health`
      verdict (step detail is not modelled; the raw payload is referenced via `raw_ref`,
      never read by the core).
- [ ] AC4: No live Dynatrace required — every test runs against recorded/representative
      DQL fixtures committed to the repo (per working agreement "pure core, mockable
      edges"). The vendor health mapping (success / failure / partial →
      `up` / `down` / `degraded`) is explicit and unit-tested.
- [ ] AC5: An **unknown/out-of-scope** monitor type (e.g. single-browser, NAM) is handled
      safely — surfaced as unsupported rather than silently mis-normalized — so adding a
      future normalizer is purely additive. A test asserts this.

## Resolved Questions
- Monitor types in scope: **HTTP + browser clickpath** (single-browser + NAM deferred).
  PO-approved at refinement, 2026-06-25.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §5/§7/§8. Status: draft.
- 2026-06-25: refined for Sprint 4. Scope fixed to HTTP + browser clickpath; AC1–AC5
  finalized and made testable; open question resolved. Estimate held at 5 (HTTP-only
  would be ~3; all four types would exceed 5). Status: ready.
