---
id: STORY-040
title: Topology seed + signal→component migration — Neon as the read model
type: feature
---

## Context
Spec: dossier §7 (Option C / D6 — Neon is a **read model** seeded from Git-versioned config at boot,
via fail-fast validation + idempotent upsert keyed on stable ids) + §9 (spine) + §17 (boot). This is
the **DB-seed half** of the original STORY-040; the config-reading half (file format, loader,
validation, in-memory resolvers) is **STORY-040a** and is a prerequisite for this story.

**Why separate from the orchestration's needs:** STORY-016a (orchestration) resolves signal→component
+ thresholds from the in-memory config (STORY-040a) and does NOT require the DB seed. THIS story
exists so the **spine read-model is populated** — so the dashboard (`GET /api/v1/components`) shows
real components and the spine matches the config. It also adds the spine's missing signal→component
link (the schema has `signals.app_id` + `components.app_id` but NO signal→component column).

## Description (to refine before its sprint)
- **Migration:** add the signal→component link to the spine (likely a `component_id` FK on `signals`,
  or a `mappings` table) — a real Alembic migration; FK-direction must hold (spine boundary).
- **Boot seed:** a composition boot step that takes the `Config` from STORY-040a and performs an
  **idempotent upsert** of apps / components / signals (+ the signal→component link) into Neon, keyed
  on stable ids — re-running boot on unchanged config is a no-op. Strict fail-fast on validation
  failure (no partial seed).
- Optionally a spine-backed topology read (signals/components from Neon) if a consumer needs it beyond
  the in-memory resolver.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: a migration adds the signal→component link; `check_fk_direction.py` stays green (the spine
      never FKs into a feature; the new link is spine-internal).
- [ ] AC2: the boot seed idempotently upserts apps/components/signals from the loaded config; a second
      run on unchanged config changes nothing (asserted against a throwaway DB).
- [ ] AC3: invalid config halts the seed fail-fast with a clear error (no partial write).
- [ ] AC4: `GET /api/v1/components` returns the seeded components after a boot seed (end-to-end on the
      throwaway DB).
- [ ] AC5: full SIX-command DoD gate green; blast radius resolved.

## Open Questions
- signal→component link shape: `component_id` FK on `signals` (1 signal → 1 component) vs a `mappings`
  table (confirm cardinality at refinement; the dossier implies one component per signal).
- Where the boot seed is invoked (app startup lifespan vs a separate release step like migrations).
- Estimate (likely 5).

## History
- 2026-06-28: created from Sprint 15 planning; reframed at Sprint 16 planning to the DB-seed half after
  STORY-040a (config layer) was split off. Depends on STORY-040a. Status: draft.
