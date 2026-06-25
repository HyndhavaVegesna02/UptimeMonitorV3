---
id: STORY-024
title: Core pipeline stages 3–4 — anti-flap + decide
type: feature
---

## Context
Spec: dossier §10 (stages 3–4) + §12 (proposal lifecycle) + §7 (per-app config / mapping).
Zone 4. The second half of the core pipeline, split from the original STORY-010 (which read
as an 8). Depends on **STORY-010** (collapse + streak provide the streak length this consumes).

## Description
In `core/services/` (the pipeline module): two pure stages turning a streak into a status
decision.
- **anti-flap** — pure lookup from streak length → proposed status, driven by per-app config
  thresholds (dossier §10): ≥5 failing → major, ≥3 → partial, ≥2 → degraded, a single failure
  → internal warning (logged, never published), ≥2 passes → operational; a sustained `degraded`
  streak → degraded-performance. Thresholds resolve component → app → that app's block.
- **decide** — compare proposed status to the component's current published status: same →
  nothing; worse → a degradation **proposal** (the human-approval gate); better → a recovery
  (auto-publishes). Also reconciles open proposals and computes the per-component skew flag
  (Tier-2 item 7).

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: `anti-flap` maps streak length → proposed status per §10 thresholds, resolved from
      per-app config (component → app → block). Unit-tested with canonical fixtures.
- [ ] AC2: Severity-ordered direction: worse → degradation proposal (human gate), better →
      recovery (auto-publish), same → nothing. Tested.
- [ ] AC3: Open-proposal reconciliation + the per-component skew flag behave per §10/§12. Tested.
- [ ] AC4: Pure and provider-blind — no vendor/HTTP/SQL imports; `lint-imports` green; tests
      use in-memory canonical fixtures; proposal domain types live in `core/domain/`.

## Open Questions
- **Per-app config mechanism**: how are thresholds loaded/resolved (component → app → block)?
  `config/apps/*.yaml` seeded into Neon (§7) does not exist yet — does this story build a
  minimal config-resolution port + fake, or is config loading a separate prerequisite story?
- Proposal domain types + how "current published status" is read (a port? the components
  table?) — confirm the seam against §12 (STORY-012 proposal lifecycle) to avoid overlap.

## History
- 2026-06-25: created by splitting STORY-010 at refinement (the original four-stage story was
  ≥8). This is stages 3–4. Status: draft — two open questions (config mechanism, proposal seam)
  MUST be resolved at refinement before it can enter a sprint. Proposed estimate: 5.
