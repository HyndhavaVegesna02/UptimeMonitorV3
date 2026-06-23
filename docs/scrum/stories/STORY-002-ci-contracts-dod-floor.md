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
- [x] AC1: `lint-imports` exits 0 on the STORY-001 skeleton, with all three contracts
      present and active (core-independence, core-internal-layering, adapter-independence).
- [x] AC2: A deliberately-introduced forbidden import (e.g. `src/core/services` importing
      `src/adapters` or `sqlalchemy`) makes `lint-imports` exit nonzero — proven by a test
      or a documented demonstration, then reverted. (The contract actually bites.)
- [x] AC3: `scripts/check_fk_direction.py` exists and exits 0 against a freshly-migrated
      (currently empty) database; it reads real FKs from `information_schema`, uses the
      §9 SPINE allowlist, and reports any spine→feature FK as a violation.
- [x] AC4: Both `lint-imports` and `python scripts/check_fk_direction.py` are listed in
      the Definition of Done and run by the bare commands shown there.
- [x] AC5: A unit test covers the FK-direction checker's violation logic (given a fake
      set of FKs including a spine→feature edge, it flags exactly that edge) so the gate
      itself is tested, not just asserted.

## Open Questions
<!-- none — ready -->

## History
- 2026-06-23: drafted from YOURTEAM_INCEPTION.md §8 + dossier §4/§9; refined to ready for Sprint 0.
- 2026-06-23: implemented (commits 3c030c9, a69d3eb, efc4c69, 4c4a3ac, 2c5f9c8, eff37c9).
  import-linter needed `include_external_packages = true` (forbidden set names sqlalchemy/httpx).
  Dossier §4's vendor subpackage names (`...inbound.dynatrace`) don't exist yet → contracts use
  the real packages `src.adapters.{inbound,outbound,persistence}`. Spec review PASS (all AC MET,
  AC2 negative demonstration independently reproduced); quality review APPROVE (FK SQL direction
  confirmed correct). DoD gate: pytest 0, lint-imports 0 (3 kept), FK-check 0. Marked Done.
- 2026-06-23: QUALITY-MINORS (non-blocking notes):
  (1) `scripts/check_fk_direction.py` — composite/multi-column FKs make `constraint_column_usage`
      emit one row per referenced column → duplicate (source,target) pairs inflate the "N checked"
      count (direction logic unaffected). `SELECT DISTINCT` would tidy it. Cosmetic; no composite
      FKs exist yet — revisit if/when STORY-006 adds any.
  (2) The function-local `import psycopg` (keeps the pure `find_violations` path driver-free for the
      unit test) is deliberate — worth a one-line comment so a future reader doesn't "fix" it.
  Candidate tiny chore; not blocking.
- 2026-06-23: NOTE — `core-internal-layering` and `adapters-independence` contracts are currently
  vacuously green (skeleton has no real imports). They begin to bite once real code lands in
  zones 1–4. Expected and correctly configured.
