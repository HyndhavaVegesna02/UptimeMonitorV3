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

## Resolved Questions (sprint-11 planning, 2026-06-27)
- **Ruleset breadth → MINIMAL.** `[tool.ruff.lint]` select = the formatter + isort (`I`) + pyflakes
  (`F`) + the pycodestyle essentials (`E`, `W`) only — NOT the broad rule families (no `B`/`UP`/`SIM`/
  etc. this round). The goal is to kill the recurring cosmetic-minor class (trailing blanks, import
  order) and catch dead/unused imports, not run a style crusade or trigger a large noisy first pass.
  Broadening the ruleset can be its own later story if it earns its keep.
- Line length: match the codebase's existing convention (set `line-length` to the prevailing value so
  the first `ruff format` pass does not reflow swathes of correctly-sized code).

## History
- 2026-06-27: created from Sprint 10 retro (recurring cosmetic-minor friction; ruff approved as a DoD
  gate). Status: draft pending the ruleset question.
- 2026-06-27 (sprint-11 planning): ruleset resolved to MINIMAL (format + I + F + E/W); line-length
  matches the codebase. Estimate held at 2 (mechanical one-pass reformat + config + DoD/CLAUDE.md
  wiring across several files). Status: ready → committed to Sprint 11. Sequenced FIRST so its
  reformat subsumes the cosmetic parts of STORY-031/032.
