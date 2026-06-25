---
id: STORY-028
title: Core pipeline stage 3 — anti-flap
type: feature
---

## Context
Spec: dossier §10 (stage 3, anti-flap). Zone 4. Split from STORY-024 at refinement (its other
half, **decide** (stage 4), genuinely needs the proposal lifecycle and stays in STORY-024 as
draft). Anti-flap is a PURE lookup with no proposal/config-loading dependency — its per-app
thresholds are INJECTED as a value object (the same pattern STORY-010 used for `maintenance` and
STORY-011 for `interval`/`window`), so config loading (`config/apps/*.yaml` → Neon, §7) is deferred.
Consumes `Streak` (STORY-010: health + length).

## Description
In `core/services/pipeline.py` (or a sibling pipeline module): `anti_flap` maps a `Streak` +
injected per-app thresholds → a status decision, per dossier §10:
- a FAILING (`down`) streak: `>=` major-threshold → `major_outage`; `>=` partial-threshold →
  `partial_outage`; `>=` degraded-threshold → `degraded`; a SINGLE failure (length 1, below the
  degraded threshold) → an **internal warning** (logged, NEVER published — a distinct outcome, not
  a published `ComponentStatus`).
- a sustained `degraded` streak → `degraded` (degraded-performance).
- a PASSING (`up`) streak `>=` recovery-threshold → `operational`.
- anything below all thresholds (e.g. a not-yet-confirmed streak) → **nothing** (no proposed status).

The default thresholds (dossier §10): major=5, partial=3, degraded=2, recovery=2 — but these are
supplied via the injected thresholds value object, NOT hard-coded. The `component → app → block`
resolution that produces the thresholds is config loading and is OUT OF SCOPE here.

A small result type distinguishes the three outcomes: a proposed `ComponentStatus`, an
internal-warning marker, or nothing. Model it cleanly (your call: a frozen result type or a
`ComponentStatus | None` plus a separate warning signal) — the three outcomes must be
distinguishable and tested.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: A failing (`down`) streak maps to a proposed status by length against the INJECTED
      thresholds: `>=` major → `major_outage`; `>=` partial → `partial_outage`; `>=` degraded →
      `degraded`. Unit-tested with in-memory fixtures at and around each boundary.
- [ ] AC2: A single failure (length 1, below the degraded threshold) yields an INTERNAL WARNING — a
      distinct outcome that is never a published `ComponentStatus`. A sustained `degraded` streak
      yields `degraded`. A passing (`up`) streak `>=` recovery yields `operational`. A streak below
      all thresholds yields NOTHING (no proposed status). All tested.
- [ ] AC3: Thresholds are INJECTED (a value object), never read from config/DB here; `anti_flap`
      is pure and provider-blind (no vendor/HTTP/SQL imports); `lint-imports` green; tests need no
      live services.
- [ ] AC4: Boundary + degenerate inputs are defined and tested (sprint-6 + sprint-7 agreements):
      streak length exactly at each threshold, just below, and length 0/1; the three failing
      sub-thresholds in severity order. No crash, no silent mis-bucketing.

## Resolved Questions
- Per-app config: thresholds are INJECTED as a value object; config LOADING (component→app→block,
  §7) is deferred to a later config story — NOT built here. (PO-approved split, 2026-06-25.)
- Proposals / "current status" / reconciliation: OUT OF SCOPE — that is the `decide` stage,
  STORY-024.

## History
- 2026-06-25: created by splitting STORY-024 at refinement (anti-flap is shippable now with
  injected thresholds; decide needs proposals). Stage 3 only. AC1–AC4 finalized. Status: ready.
