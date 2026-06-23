---
id: STORY-002
title: CI contracts = the DoD floor
type: chore
---

## Context
Spec: `uptime-monitor-v3-design.html` §4 (import-linter contracts, verbatim config
shown) and §9 (the schema FK-direction CI check, with example `test_schema_boundary.py`).
This story makes the architecture's non-LLM floor real. Per the working agreement,
"boundary violations are build failures, not review comments" — so these two checks
must exist, be wired into the DoD, and pass green on the empty skeleton from STORY-001,
so that every later story inherits a working, enforced boundary.

## Description
1. Configure **import-linter** with the three contracts from dossier §4:
   - `core-independence` (type: forbidden) — `src.core` may not import
     `src.adapters`, `src.composition`, `src.api`, `sqlalchemy`, `httpx`.
   - `core-internal-layering` (type: layers) — `src.core.services` →
     `src.core.ports` → `src.core.domain` (higher may import lower, never the reverse).
   - `adapters-dont-cross` (type: independence) — the inbound/outbound/persistence
     adapter packages may not import one another. (Reference the adapter subpackages
     that exist after STORY-001; if a named vendor subpackage from the dossier example
     does not exist yet, use the actual adapter package paths created in STORY-001 and
     note the mapping — the contract must run green, not reference phantom modules.)
   - Invocation must be the bare command `lint-imports` (the DoD command).
2. Implement `scripts/check_fk_direction.py` — the schema FK-direction check from
   dossier §9. It reads the actual foreign keys from a migrated database's
   `information_schema` and fails (nonzero exit) if any SPINE table references a
   non-SPINE (feature) table. The SPINE allowlist is the explicit set from §9
   (`apps, signals, components, observations, watermarks, rejected_observations,
   problem_signals, status_proposals, approval_events, publications,
   maintenance_windows`). On the empty skeleton (no tables yet) it must exit 0
   (zero FKs → zero violations). It must run without requiring real Neon — point it
   at a `DATABASE_URL` (Dockerized Postgres in Sprint 0 / CI).
3. Wire both commands into `.scrum/definition-of-done.md` (already drafted) and confirm
   they execute via the bare commands the DoD lists.

## Acceptance Criteria
- [ ] AC1: `lint-imports` exits 0 on the STORY-001 skeleton, with all three contracts
      present and active (core-independence, core-internal-layering, adapter-independence).
- [ ] AC2: A deliberately-introduced forbidden import (e.g. `src/core/services` importing
      `src/adapters` or `sqlalchemy`) makes `lint-imports` exit nonzero — proven by a test
      or a documented demonstration, then reverted. (The contract actually bites.)
- [ ] AC3: `scripts/check_fk_direction.py` exists and exits 0 against a freshly-migrated
      (currently empty) database; it reads real FKs from `information_schema`, uses the
      §9 SPINE allowlist, and reports any spine→feature FK as a violation.
- [ ] AC4: Both `lint-imports` and `python scripts/check_fk_direction.py` are listed in
      the Definition of Done and run by the bare commands shown there.
- [ ] AC5: A unit test covers the FK-direction checker's violation logic (given a fake
      set of FKs including a spine→feature edge, it flags exactly that edge) so the gate
      itself is tested, not just asserted.

## Open Questions
<!-- none — ready -->

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §4/§9; refined to ready for Sprint 0.
