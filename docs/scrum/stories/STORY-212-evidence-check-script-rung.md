---
id: STORY-212
title: Land the evidence-artifact rule at the SCRIPT rung (mutation + provenance helper)
type: chore
points: 3
status: done
filed: 2026-08-01
sprint: 70
---

## Context

Six retro amendments across five sprints all encode one idea — *an evidence
artifact that cannot fail is not evidence*:

| Amendment | Sprint | Symptom it was written for |
| --------- | ------ | -------------------------- |
| A1        | 62     | reality gate reported PASS on two empty dumps |
| A1-ref    | 63     | worktree proof ran the main tree's code (editable install) |
| A3        | 63     | three proofs returned identical on both sides, three mechanisms |
| A4        | 63     | a mutant `expand_scenario` passed all 30 new tests |
| A7        | 64     | harness printed correct values, asserted one AC, exited 0 always |
| A9        | 65     | two tests green against a mutation that broke the guarded behaviour |

Each landed at the CHECKLIST rung, and each landed *because the previous one did
not hold*. That is the enforcement ladder failing in the direction it was built to
prevent: the lesson is mechanical, the rung taken was prose.

Every one of the six retros that produced them names the script rung and declines
it, for reasons that are now removed or answerable:
- sprint-63 retro lists "the import-provenance helper script — the mechanical rung
  A1/A3 keep declining to take" under future work. It was then partly taken:
  `tools/import_provenance.py::assert_import_root` exists (STORY-187).
- A1-ref and A3 both declined the script rung citing the mid-sprint tooling freeze
  and the ban on ad-hoc skill-script edits outside a story. The freeze now carries
  an enforcement-ladder exemption (2026-08-01 amendment) and this IS the story.

The stated objection — "a reality gate is bespoke per story, so no script can judge
whether a given assertion could have diverged" — is true and is not what this story
claims. A script cannot decide whether a proof was *meaningful*. It can mechanise
the three checks that are not bespoke at all: did the artifact exit non-zero on bad
input, did the two sides differ, did the mutation turn anything red.

## Description

Add `tools/evidence_check.py`: a dev-only helper (never in the production image,
same placement rule as `tools/import_provenance.py`) providing the mechanical half
of the collapsed evidence rule now in `.scrum/checklists/implementer.md`.

Three subcommands, each a genuine check with a non-zero exit — the tool must obey
the rule it enforces:

1. `falsify <artifact> --bad-input <spec>` — run the artifact against deliberately
   bad evidence and assert it exits non-zero. An artifact that exits 0 on bad input
   is reported as NOT A GATE.
2. `two-sided --left <cmd> --right <cmd>` — run both sides, record both outcomes,
   and FAIL when they are identical, whatever the value. Wraps
   `assert_import_root` when the declared mechanism is import provenance.
3. `mutate <target> --tests <selector>` — apply a declared mutation, run the
   selected tests, report which went RED, restore, and assert `git diff` is empty.
   Zero RED exits non-zero.

The point is not to remove judgment. It is that the three most common mechanical
failures stop depending on an agent remembering a paragraph.

## Acceptance Criteria

- [x] AC1: `tools/evidence_check.py` exists with the three subcommands, is
      importable and runnable via `python tools/evidence_check.py <cmd>`, and lives
      outside `backend/src/`. **The isolation is asserted by a NEW concrete test, because
      no existing mechanism covers it** (corrected 2026-08-13 at plan verification: all
      nine import-linter contracts are over `src.*`, `pyproject.toml` never names `tools`,
      and the only `tools` reference in the suite is `conftest.py:37`, which ADDS it to
      `sys.path`). The assertion: no file under `backend/src/` contains an import of
      `tools` — a grep-shaped test in the style of the existing ZR guards, not a tenth
      import-linter contract.
      Landed: `backend/tests/test_tools_isolation.py::find_tools_imports` (AST-based, not
      text grep — RC-1's `__pycache__`/count-drift concern does not apply) plus
      `test_no_backend_src_file_imports_tools`, `test_find_tools_imports_detects_offender`,
      `test_find_tools_imports_ignores_unrelated_imports`,
      `test_find_tools_imports_empty_dir_returns_empty_list`.
- [x] AC2: `falsify` exits non-zero when the artifact under test exits 0 on bad
      input, and zero when the artifact correctly fails. Both directions tested.
      Landed: `check_falsify` in `tools/evidence_check.py`; both directions in
      `backend/tests/test_evidence_check.py`
      (`test_check_falsify_reports_not_a_gate_when_artifact_exits_zero_on_bad_input`,
      `test_check_falsify_passes_when_artifact_correctly_fails_on_bad_input`); live CLI
      demonstration recorded in the implementer report (AC5).
- [x] AC3: `two-sided` exits non-zero when both sides produce identical outcomes,
      including the case where both sides are correct-looking. Tested with a pair
      that genuinely differs (passes) and a pair that does not (fails).
      Landed: `check_two_sided` + `check_two_sided_import_provenance` (the
      `assert_import_root` wrap, AC6); both directions and the "same exit code,
      different stdout" / "different command, identical outcome" edge cases in
      `backend/tests/test_evidence_check.py`.
- [x] AC4: `mutate` exits non-zero when zero tests go RED, restores the tree, and
      asserts **`git diff -- <the mutated target>`** is empty afterwards; a failure to
      restore is itself a non-zero exit, never a silent pass. **Scoped to the target, not
      the whole tree** (corrected 2026-08-13 at plan verification): a whole-tree emptiness
      check fails on any legitimately dirty sprint tree — including right now, with three
      modified story files and an untracked sprint directory — so the tool would exit
      non-zero on every correct run. The restore claim is about what `mutate` touched.
      Landed: `check_mutate` (patch file, `git apply`/`git apply -R`, targets parsed from
      the patch's own `+++ b/<path>` headers via `parse_patch_targets`). Writing the
      zero-RED test surfaced a real bug — `run_pytest_selectors` counted "PASSED" as RED,
      so a behaviour-preserving mutation reported a false red-for-the-wrong-reason; fixed
      (narrowed to `FAILED`/`ERROR` only) before this AC could be marked done.
- [x] AC5: **The tool is subjected to its own rule.** Each of the three
      subcommands is fed deliberately bad input and shown to fail, and that
      demonstration is recorded on the board — per the checklist rule this story
      is landing the mechanism for.
      Demonstrated via the real CLI (`evidence_check.main`), one bad-input case per
      subcommand, each hitting a genuinely different branch (not two demonstrations
      collapsing into one, per STORY-220's own caution) — full tails and self-critique
      in the implementer report.
- [x] AC6: `assert_import_root` (`tools/import_provenance.py`, STORY-187) is
      reused, not reimplemented.
      Landed: `check_two_sided_import_provenance` imports and calls
      `assert_import_root`/`WrongImportRootError` directly; proven not reimplemented by
      `test_check_two_sided_import_provenance_wraps_assert_import_root_not_reimplemented`
      (monkeypatches the real function and observes its output surface unchanged).
- [x] AC7: `.scrum/checklists/implementer.md` and
      `.scrum/checklists/quality-review.md` point at the tool for the mechanical
      half, and the prose shrinks accordingly — the checklist gets shorter, not
      longer, as a result of this story.
      Landed: `implementer.md` 115 -> 109 lines, `quality-review.md` 126 -> 120 lines
      (total 241 -> 229). Flagged to the orchestrator for verification since `.scrum/` is
      orchestrator-owned.
- [x] AC8: Full 8/8 DoD gate green at the final HEAD.
      Verified: backend 5/5 (789 passed/0 skipped; 9 contracts kept; ruff clean;
      cfn-lint exit 0) + frontend 3/3 (363 passed; build; lint) — see report for tails.

## Open Questions — BOTH RESOLVED at sprint-70 refinement (2026-08-13)

1. **`mutate`'s mutation format: a PATCH FILE**, applied with `git apply` and reverted
   with `git apply -R`. Chosen because it is the most auditable of the three (the mutation
   is itself a reviewable artifact that can be committed alongside the red/green output
   tails, which is the whole point of this story), and because revert-by-inverse-patch is
   the only one of the three that cannot half-apply silently — `git apply` is atomic, where
   a sed expression run twice is not. A declared target+value cannot express the multi-line
   mutations this project's proofs actually use (STORY-216's three ZR-8 edits were all
   multi-line). **This is the entire interface of subcommand 3**; it was unresolved in the
   story, the backlog and the plan until plan verification flagged it.
2. **It belongs in `tools/` (project-local).** Settled by AC6: the tool must reuse
   `tools/import_provenance.py::assert_import_root`, which is project-local. Splitting a
   generic core into the skill would either duplicate that helper or make the skill depend
   on a project file, and the skill is project-generic by rule. If a second project ever
   needs this, promote it then, with two real call sites to generalise from.

## History
- 2026-08-01: drafted alongside the checklist collapse that removed ~85 lines of
  prose covering A1/A1-ref/A3/A4/A7/A9. The collapse kept the rule; this story
  moves its mechanical half to the rung six retros said it belonged on.
- 2026-08-13: **REFINED and SIZED 3 at sprint-70 planning.** Both open questions resolved
  above. AC1 and AC4 corrected after pre-lock plan verification found AC1 named a mechanism
  that does not exist and AC4 was infeasible as literally written. PO-directed into sprint 70
  at the sprint-69 review (RC-1/RC-7 — agent evidence died with the agent three times in one
  sprint): "prioritise it rather than restating the lesson a fourth time." **Definition of
  Ready met: approved AC, estimate, no unresolved questions.**
