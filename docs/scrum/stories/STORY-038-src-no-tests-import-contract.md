---
id: STORY-038
title: 5th import-linter contract — production src must not import tests
type: chore
---

## Context
Surfaced by the Sprint 13 review of STORY-014b: `composition/app.py` imported
`from tests.fakes import FakeComponentRepository` into PRODUCTION code (a `src -> tests`
dependency that would `ImportError` in a deployed artifact with `tests/` stripped). It was a
quality-review MAJOR that **slipped the mechanical DoD floor** because no import-linter contract
forbids `src` importing `tests`. Per the project's "boundary violations are build failures, not
review comments" principle (working-agreements.md 2026-06-23), this class should be caught by the
gate, not by a reviewer. This chore adds that contract (a retro tooling decision, 2026-06-28).

## Description
Add a 5th `import-linter` contract to `[tool.importlinter]` in `pyproject.toml` forbidding any
`src.*` module from importing the `tests` package — e.g. a `forbidden` contract with
`source_modules = ["src"]`, `forbidden_modules = ["tests"]` (verify the exact shape against the
import-linter docs; `tests` must be importable as a top-level package for the contract to resolve,
as it already is under the editable install). The contract COUNT goes 4 -> 5, so the **command-sync
agreement applies**: update `.scrum/definition-of-done.md` (the `lint-imports` line / contract count)
AND `CLAUDE.md` (the §4 contract count + the contract list) in the SAME commit. Update
`architecture-boundary.md` (it enumerates the contracts) at the DoD blast-radius step.

## Acceptance Criteria (draft — refine before its sprint)
- [ ] AC1: a 5th import-linter contract forbids `src` importing `tests`; `lint-imports` reports
      **5 kept / 0 broken** on the current tree.
- [ ] AC2: the contract is proven non-vacuous — a temporary `from tests... import ...` inside a
      `src/` module makes `lint-imports` report the new contract BROKEN (revert after; note in History).
- [ ] AC3: command-sync — `.scrum/definition-of-done.md` + `CLAUDE.md` updated in the same commit
      (contract count 4 -> 5); `architecture-boundary.md` updated + re-verified.
- [ ] AC4: full SIX-command DoD gate green.

## Resolved Questions
- **Contract shape → a `forbidden` contract** with `source_modules = ["src"]` and
  `forbidden_modules = ["tests"]` in `[tool.importlinter]` (mirrors the existing `core-independence`
  forbidden contract). The implementer VERIFIES this resolves and reports KEPT against the current
  tree; if the installed import-linter needs `tests` to be an importable package, it already is under
  the editable install. AC2's non-vacuous spike is the proof the shape works. (Resolved 2026-06-28.)
- **Estimate: 1** (one contract block + command-sync doc updates; gate-only).

## History
- 2026-06-28: created from the Sprint 13 retro (the STORY-014b `src->tests` MAJOR slipped the gate
  because no contract forbids it).
- 2026-06-28 (Sprint 14 refinement): contract shape resolved (forbidden src→tests). Status: draft → ready.
