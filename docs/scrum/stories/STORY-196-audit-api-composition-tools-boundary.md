---
id: STORY-196
title: Audit api + composition and the tools/ to src/ one-way boundary
type: chore
points: 2
status: ready
refined: 2026-07-31
---

## Context

The second measuring pass. Three surfaces the first pass deliberately leaves out:

- **`api`** (55 modules) — the widest zone by file count and the thinnest by intent. Its rules are
  about *shape*: five-file features, no feature reaching into another, no reaching past `core`.
- **`composition`** (13 modules) — the only zone allowed to see both sides, which makes it the only
  place a violation looks like ordinary work. Two composition roots exist (`run.py::main` and
  `app.py::create_app`) and sprint-64 proved they drift apart: `CONFIG_DIR` had to be set on **both**
  or neither was guarded.
- **The `tools/` → `backend/src/` one-way boundary** (17 tool modules) — `tools/` may import `src.*`,
  never the reverse, and a constant shared between them must live in `backend/src/` with `tools/`
  importing it rather than duplicating the literal (PO directive, memory `code-boundary-discipline`).
  `lint-imports` cannot see this at all: `tools/` is outside `root_package = "src"`.

That last one is the highest-yield surface in the sprint, because it is the one with **zero**
mechanical coverage today, and the repo already has a known live example of the pattern working
correctly (`tools/demo_engine/assumed_failure_codes.py` deriving from `PROVISIONAL_STATUS_MAPPING`
rather than redeclaring it) — so there is a compliant reference to measure drift against.

Depends on **STORY-194** for rule ids. Independent of STORY-195 (disjoint files), but sequenced after
it so the report shape established there is reused rather than reinvented.

## Description

Same method and same report contract as STORY-195, at
`docs/scrum/sprints/2026-07-31-sprint-66/audit-api-composition-tools.md`, plus one mechanical sweep
this pass owns: a duplicated-declaration hunt across the `tools/` ↔ `src/` boundary.

Docs and `.scrum/backlog.yaml` only. Nothing is fixed inline.

## Acceptance Criteria

- [ ] **AC1** — The report accounts for every module under `backend/src/api/` (55),
      `backend/src/composition/` (13) and `tools/` (17), each listed once with `CLEAN` or finding ids.
      The enumeration command and its output are recorded and the listed count matches it.
- [ ] **AC2** — Findings carry the same four fields STORY-195 AC2 requires (`ZR-n`, resolving
      `file:line`, `MAJOR`/`MINOR`, why the contracts pass it), and `MAJOR`s are filed as their own
      `draft` backlog stories with testable AC. `MINOR`s may be batched into one filed story.
- [ ] **AC3** — A duplicated-declaration sweep across the one-way boundary is run and **its command
      and output recorded**: every constant, literal-with-meaning, or type declared in BOTH `tools/`
      and `backend/src/` is listed with both `file:line`s and a verdict — `MUST-IMPORT-FROM-SRC`
      (a violation, filed) or `INDEPENDENT` (legitimately unrelated, with the reason). Absence of
      duplicates is a valid result **only if** the sweep is shown to be capable of finding one:
      demonstrate it against a known-shared value (the failure-code mapping is the reference case).
- [ ] **AC4** — The `api` pass explicitly reports on feature shape: whether any feature module reaches
      outside its own directory other than to `core` and `api/v1/_shared`, and whether the five-file
      feature convention holds per feature — deviations listed by feature name, with the count.
- [ ] **AC5** — The `composition` pass explicitly reports whether the two composition roots
      (`run.py::main`, `app.py::create_app`) agree on every setting where disagreement changes
      behaviour, `CONFIG_DIR` included, with `file:line` for each side. A divergence is a `MAJOR`.
- [ ] **AC6** — `CLEARED` entries are recorded with reasons (STORY-195 AC4's rule), this story's diff
      touches no file under `backend/src/`, `frontend/` or `config/`, and the five backend DoD commands
      exit 0 with a zero skip count recorded.

## Open Questions

None.

## History

- 2026-07-31: drafted and refined in sprint-66 planning. 2 points rather than 3 despite covering more
  files: `api` is 55 near-identical five-file features, so per-file judgement is far cheaper than in
  `core`, and the report contract is inherited from STORY-195 rather than designed here.
