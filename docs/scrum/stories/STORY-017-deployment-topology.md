---
id: STORY-017
title: Deployment topology
type: chore
---

## Context
Spec: dossier §17 (deployment topology). The five pieces in three categories; migrations
as a separate release step before serving.

## Description
Backend on Railway (single instance; `alembic upgrade head` as a release step on the
Neon DIRECT connection, then app boots: seed topology → start scheduler → serve on the
pooled connection). Frontend on Vercel. Sock Shop on Railway service #2 + the toggle-able
failure shim in front of one monitored route. Secrets in Railway env (config references
env var NAMES, never values). Tuned demo cadence (~1-min monitors, short poll interval).
CORS restricted to the Vercel origin.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: A push deploys via the migrate-release-then-serve flow.
- [ ] AC2: A failed migration halts the deploy and leaves the old container serving
      (fail-safe, not crash-loop).
- [ ] AC3: The demo thread (STORY-016) runs on the deployed infra.
- [ ] AC4: Secrets live in Railway env; CORS restricted to the Vercel origin.

## Open Questions
- Confirm Railway/Vercel/Neon account access and the secret-provisioning plan at refinement.

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §17. Status: draft — refine before its sprint.
