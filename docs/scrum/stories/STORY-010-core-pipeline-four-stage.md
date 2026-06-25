---
id: STORY-010
title: Core pipeline stages 1–2 — collapse + streak
type: feature
---

## Context
Spec: dossier §10 (core logic pipeline), stages 1–2 only. Zone 4. The constant core's
brain — pure, provider-blind. Nothing here mentions Dynatrace/DQL.

**Split note (2026-06-25):** the original STORY-010 ("four-stage pipeline") read as an 8
once per-app config resolution + proposal generation/reconciliation were counted, so it was
split at refinement. This story is the first, self-contained half — stages 1 (collapse) and
2 (streak), which need no per-app config and produce no proposals. Stages 3–4 (anti-flap +
decide) are **STORY-024**.

## Description
In `core/services/` (new pipeline module): two pure stages over canonical observations.
- **collapse** — one signal's per-location observations for a cycle → ONE verdict
  (dossier §10): all-up → `up`, all-down → `down`, otherwise → `degraded`. Maintenance is
  checked here and EXCLUDED from the verdict (planned work, neither up nor down — V2 FR-8); a
  maintenance cycle short-circuits the rest of the pipeline (yields a maintenance marker, not a
  health verdict). Maintenance status for a cycle is an INJECTED input/predicate (pure core —
  no table query here; a fake supplies it in tests).
- **streak** — count consecutive verdicts of the same health, reading backward, over
  NON-maintenance verdicts only (dossier §10; governs displayed status, never the availability
  ratio — P4/D-3).

New canonical domain types this needs (e.g. a `Verdict` carrying signal_key, cycle instant,
`health`, and a maintenance marker) live in `core/domain/`.

## Acceptance Criteria (refined — PO-approved 2026-06-25)
- [ ] AC1: `collapse` maps a cycle's per-location observations to one verdict per §10:
      all `up` → `up`; all `down` → `down`; any mix / any non-up (down or degraded) alongside
      others → `degraded`. Unit-tested with in-memory canonical fixtures (single + multi
      location).
- [ ] AC2: A cycle flagged as under maintenance is EXCLUDED from the verdict and
      short-circuits the pipeline (no up/down verdict produced), and maintenance verdicts are
      excluded from the streak. Maintenance status is an injected input (no live table). Tested.
- [ ] AC3: `streak` counts consecutive same-health verdicts reading backward over
      non-maintenance verdicts only; a health change (or a maintenance gap per the §10 rule)
      resets/terminates the count. Tested with canonical fixtures.
- [ ] AC4: Pure and provider-blind — no vendor / HTTP / SQL imports; `core-internal-layering`
      + `core-independence` stay green (`lint-imports`); tests need no live services. Any new
      domain type lives in `core/domain/`.

## Resolved Questions
- Per-app config thresholds / resolution mechanics — OUT OF SCOPE here; moved to STORY-024
  (anti-flap) where they belong. This story has no config dependency. (PO-approved split,
  2026-06-25.)

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §10. Status: draft.
- 2026-06-25: refined for Sprint 6. Split — re-scoped to stages 1–2 (collapse + streak),
  re-estimated 5 → 3; stages 3–4 moved to STORY-024. AC1–AC4 finalized. Status: ready.
