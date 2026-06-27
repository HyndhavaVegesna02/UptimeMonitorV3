---
id: STORY-033
title: Add ruff (format + import-sort) as a mechanical DoD gate
type: chore
---

## Context
Follow-up from Sprint 10 retro (tooling decision). A recurring class of non-blocking cosmetic minors —
trailing blank lines, unsorted/mixed imports — reaches code review most sprints and accumulates into
follow-up chores (STORY-031, STORY-032). Adding `ruff` as a formatter + import sorter catches them
mechanically before review. Tooling changes are sanctioned only at planning/retro; this was approved
at the Sprint 10 retro (see working-agreements.md, 2026-06-27).

## Acceptance Criteria (refined — PO-approved 2026-06-27)
- [ ] AC1: `ruff` is added to the dev extras in `pyproject.toml` and configured (a `[tool.ruff]`
      section): target Python 3.13, line length matching the codebase, import sorting (isort rules)
      and the formatter enabled. Config is committed.
- [ ] AC2: The existing tree is formatted/import-sorted in ONE mechanical pass (`ruff format` +
      `ruff check --fix` for import order), with NO behaviour change — `pytest` (full suite) and
      `lint-imports` stay green, and the diff is formatting-only (no logic edits).
- [ ] AC3: `ruff check` and `ruff format --check` are wired into `.scrum/definition-of-done.md` as
      gate commands (exit 0 required) and documented in `CLAUDE.md` "Key commands" + the tooling
      inventory — in the SAME commit (the command-sync working agreement). The root
      `definition-of-done.md` stays a one-line pointer.
- [ ] AC4: All DoD gates green after the change: the four existing (`pytest`, `lint-imports`,
      `check_fk_direction.py`, `alembic upgrade head`) plus the two new ruff commands, each exit 0.

## Open Questions
- Should ruff's lint ruleset be broad (many rule families) or minimal (format + isort + a small safe
  core like pyflakes/pycodestyle-essentials)? Lean MINIMAL to avoid a large noisy first pass and
  bikeshedding; the goal is killing the cosmetic-minor class, not a style crusade. Confirm at planning
  if it needs to be broader.

## History
- 2026-06-27: created from Sprint 10 retro (recurring cosmetic-minor friction; ruff approved as a DoD
  gate). Status: ready — one open question (ruleset breadth) with a clear default; estimate: 2 (the
  one-pass reformat + DoD/doc wiring touches several files, but is mechanical). Re-confirm estimate at
  planning.
