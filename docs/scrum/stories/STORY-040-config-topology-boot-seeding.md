---
id: STORY-040
title: §7/§17 config + boot seeding — signal→component topology + per-app thresholds
type: feature
---

## Context
Spec: dossier §7 (per-app config: anti-flap thresholds, approval SLA, gap policy) + §17 (boot:
strict fail-fast validation → idempotent upsert of seeded topology, keyed on stable ids) + §9
(topology = apps/signals/components/mappings). Surfaced by Sprint 15 planning: the **pipeline
orchestration is blocked** on two unbuilt foundations —
1. **signal→component mapping** — the schema has NO link from `signal_key` to a component (`signals`
   only carries `app_id`); nothing can say which component an observation feeds.
2. **per-app `AntiFlapThresholds`** — `apps.config` (JSONB) exists but nothing reads it; `anti_flap`
   needs injected thresholds and there is no config loader.

This story builds that foundation so STORY-016a (orchestration) can run.

## Description (to refine before Sprint 16)
Likely scope — split if it estimates > 5:
- A `config/` source (repo-root, per CLAUDE.md's reserved `config/`) describing apps, signals,
  components, and the **signal→component mapping**, plus per-app behavioral config (anti-flap
  thresholds / SLA / gap policy), referencing env var NAMES not secrets.
- A boot step (composition): strict fail-fast **validation** of the config, then an **idempotent
  upsert** of the seeded topology into the spine tables, keyed on stable ids (dossier §17). Decide
  whether the signal→component mapping needs a new spine column/table (a MIGRATION) or lives in
  config + a runtime resolver — this is the central design question for refinement.
- A core **topology read port** (e.g. resolve `signal_key → component_id`, list a component's
  signals) + adapter, and **per-app threshold resolution** (`component → app → AntiFlapThresholds`),
  both consumable by the orchestration. Defaults per dossier §10 where config is absent.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: config is loaded + validated fail-fast at boot; invalid config halts with a clear error.
- [ ] AC2: seeded topology is upserted idempotently (re-running boot is a no-op on unchanged config).
- [ ] AC3: a topology resolver maps `signal_key → component_id`; per-app `AntiFlapThresholds` resolve
      from config (with §10 defaults), each tested.
- [ ] AC4: FK-direction + full SIX-command gate green; if a mapping column/table is added, it is a
      real Alembic migration and the spine boundary holds.

## Open Questions
- Does signal→component live in config + resolver only, or also as a spine column/table (migration)?
- Boundaries of §7 (thresholds/SLA/gap) vs what the orchestration actually needs first — may split.
- Estimate (likely 5+; split candidate).

## History
- 2026-06-28: created from Sprint 15 planning (the orchestration's unbuilt prerequisite). Status:
  draft — refine (and likely split) before Sprint 16.
