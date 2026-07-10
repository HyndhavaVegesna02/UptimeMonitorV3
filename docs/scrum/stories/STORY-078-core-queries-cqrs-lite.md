---
id: STORY-078
title: core/queries/ — move the availability read-model into a fenced 4th core subpackage (CQRS-lite, proposal §8)
type: chore
---

## Context
From the accepted 2026-07-10 API restructure proposal, §8 ("Deferred: core/queries/ (CQRS-lite)").
The proposal recorded this as a trigger-gated future phase; the PO has elected to trigger it now
(2026-07-10). The move names and mechanically fences the read side of the domain: the availability
derivation (a pure, no-persisted-verdicts read computation — DoD standing rule
`.scrum/definition-of-done.md`) becomes a distinct `core/queries/` subpackage, separate from the
state-changing write model in `core/services/`. This makes the P4 invariant "the pipeline never
consults availability" (today only a docstring in `core/services/availability.py`) a build failure.

Scope note (proposal §8): this story is the MOVE + the layering contract only. C's per-feature
read/write API contracts (`api-read-features-no-write-model` etc.) and the `api/dependencies.py`
ApprovalService-decoupling remain REJECTED/deferred — they fail today via a transitive chain and
cost more than they guard (proposal §5.3, §8). Do NOT add them here.

## Description
Move the availability read-model whole from `core/services/availability.py` to
`core/queries/availability.py`; add the `queries` layer to the core-internal-layering contract;
update the (few) import sites; resolve wiki blast radius. No behavior change — pure relocation +
boundary tightening.

## Acceptance Criteria
- [ ] `backend/src/core/queries/__init__.py` + `core/queries/availability.py` exist; the following
      move WHOLE from `core/services/availability.py` (deleted from there): `AvailabilityCalculator`,
      `AvailabilityResult`, `rollup_group`, `bucket_into_cycles` (and any private helpers they own).
      They keep importing `collapse` from `core/services/pipeline.py` (queries → services' pure
      functions is the allowed direction). No other logic moves; the calculation/windowing carve-up
      is explicitly NOT done (proposal §8) — the module moves intact.
- [ ] `pyproject.toml` `core-internal-layering` contract becomes
      `layers = ["src.core.queries", "src.core.services", "src.core.ports", "src.core.domain"]`.
      `lint-imports` exits 0 (**8 kept, 0 broken**): queries may import services/ports/domain;
      services may NOT import queries (verify by confirming nothing in `core/services/` imports
      `core.queries`, and `core-independence` still holds — `core.queries` is inside `src.core`, so
      vendor-freedom is inherited).
- [ ] All import sites updated to the new path: `composition/orchestrate.py` (imports
      `bucket_into_cycles`), `api/v1/availability/service.py` (imports `AvailabilityCalculator`),
      and any test imports (`backend/tests/test_availability.py` et al.). Grep-proof: no reference to
      `core.services.availability` remains anywhere.
- [ ] **Behavior frozen:** every existing test passes (tests may have their IMPORT PATH updated —
      that is a mechanical move, not a contract change — but no assertion/behavior changes). The
      availability endpoint + calculator tests still drive the same scenarios and outcomes.
- [ ] Backend six-gate DoD green; wiki blast radius resolved via the mechanical sweep (expect
      `core-pipeline-and-availability` / `canonical-types-and-ports` / `architecture-boundary` and
      any article whose `code_refs` list `core/services/availability.py` — update the path +
      re-verify; `architecture-boundary` gains the `queries` layer fact).

## Open Questions
None — mechanism fixed by proposal §8. Verified in the design panel: `skew.py` does NOT import the
calculator (the suspected self-breaking layers trap is empty); `orchestrate.py` → `core.queries` is
a legal composition→core arrow.

## References
- Proposal: `docs/superpowers/specs/2026-07-10-api-restructure-design.md` §8 (the move), §5.3 (why
  the read/write feature contracts are excluded), §2.2 (core-independence inherited).
- Layering precedent: the existing `core-internal-layering` contract (services → ports → domain).

## History
- 2026-07-10: filed + refined from proposal §8 at PO election to trigger the phase. Status: ready (3 pts).
