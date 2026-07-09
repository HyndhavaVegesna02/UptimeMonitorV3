---
id: STORY-074
title: API-zone enforcement — api-outward-independence + adapters-edge-only contracts + zone-layout meta-test
type: chore
---

## Context
From the 2026-07-10 API restructure proposal (`docs/superpowers/specs/2026-07-10-api-restructure-design.md`,
§3.4 G1, §6.3, §10 Phase 1). The adversarial verification found that NO import-linter contract today
forbids `src.api` from importing `src.adapters` / `src.composition` / `sqlalchemy` — the api zone's
defining thinness is a convention, not a build failure. Likewise nothing forbids `src.adapters` from
importing `src.api`/`src.composition`. Both candidate contracts were **empirically run against HEAD
and pass green** (0 illegal chains, 138 files, 403 deps), so this story is pure enforcement — no
source moves. The only unguarded drift risk in the new-endpoint recipe (proposal G4) is forgetting
the `api-feature-independence` module-list entry or the router aggregation; a meta-test closes it.

## Description
Add the two contracts to `pyproject.toml` exactly as specified in proposal §6.3, and add a
zone-layout meta-test that mechanically ties the `api/v1/` directory listing to the
`api-feature-independence` contract list and the v1 router aggregator.

## Acceptance Criteria
- [x] `pyproject.toml` gains the two contracts verbatim from proposal §6.3:
      `api-outward-independence` (forbidden: `src.api` → `src.adapters`, `src.composition`,
      `sqlalchemy`, `psycopg`, `httpx`) and `adapters-edge-only` (forbidden: `src.adapters` →
      `src.api`, `src.composition`). `lint-imports` exits 0 reporting **7 kept, 0 broken**.
- [x] A new `backend/tests/test_zone_layout.py` asserts: every package directory under
      `backend/src/api/v1/` whose name does NOT start with `_` (i) appears in the
      `api-feature-independence` contract's module list in `pyproject.toml`, and (ii) has its
      router included by the v1 aggregator (`backend/src/api/v1/__init__.py`). The test FAILS when
      a new feature directory is added without both registrations (proven by the test's own logic —
      it derives the expected set from the filesystem, the contract list from parsing
      `pyproject.toml`, and the mounted routes from the aggregated router; underscore-prefixed
      packages are knowingly excluded so the future `_shared` package cannot false-fail it).
- [x] Backend six-gate DoD green; wiki blast radius resolved via the mechanical sweep (note:
      `architecture-boundary.md` lists `pyproject.toml` in its `code_refs` and documents the
      contract inventory — expect it stale and update its contract count/Facts).

## Open Questions
None — the contracts are pre-verified green and quoted verbatim in the proposal.

## References
- Proposal: `docs/superpowers/specs/2026-07-10-api-restructure-design.md` §3.4 (G1, G4), §6.3, §10 Phase 1
- Precedent: STORY-038 (5th contract, src-no-tests) — same shape of story.

## History
- 2026-07-10: filed + refined from the accepted API restructure proposal (Phase 1). Status: ready (2 pts).
- 2026-07-10: Completed implementation. Final commit SHA: 6035e12
  DoD Gate Results:
  - pytest: exit 0 (534 passed in 40.33s)
  - lint-imports: exit 0 (7 kept, 0 broken)
  - python scripts/check_fk_direction.py: exit 0 (11 foreign keys checked, 0 violations)
  - alembic upgrade head: exit 0
  - ruff check .: exit 0
  - ruff format --check .: exit 0
  Wiki articles updated: architecture-boundary.md (and re-verified others: api-five-file-convention.md, config-layer.md, dev-setup-and-dod.md, frontend-zone.md, sample-mode.md).
