---
id: STORY-212
title: Land the evidence-artifact rule at the SCRIPT rung (mutation + provenance helper)
type: chore
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

- [ ] AC1: `tools/evidence_check.py` exists with the three subcommands, is
      importable and runnable via `python tools/evidence_check.py <cmd>`, and lives
      outside `backend/src/` — nothing under `backend/src/` imports it (assert with
      the existing zone/import discipline).
- [ ] AC2: `falsify` exits non-zero when the artifact under test exits 0 on bad
      input, and zero when the artifact correctly fails. Both directions tested.
- [ ] AC3: `two-sided` exits non-zero when both sides produce identical outcomes,
      including the case where both sides are correct-looking. Tested with a pair
      that genuinely differs (passes) and a pair that does not (fails).
- [ ] AC4: `mutate` exits non-zero when zero tests go RED, restores the tree, and
      asserts `git diff` is empty afterwards; a failure to restore is itself a
      non-zero exit, never a silent pass.
- [ ] AC5: **The tool is subjected to its own rule.** Each of the three
      subcommands is fed deliberately bad input and shown to fail, and that
      demonstration is recorded on the board — per the checklist rule this story
      is landing the mechanism for.
- [ ] AC6: `assert_import_root` (`tools/import_provenance.py`, STORY-187) is
      reused, not reimplemented.
- [ ] AC7: `.scrum/checklists/implementer.md` and
      `.scrum/checklists/quality-review.md` point at the tool for the mechanical
      half, and the prose shrinks accordingly — the checklist gets shorter, not
      longer, as a result of this story.
- [ ] AC8: Full 8/8 DoD gate green at the final HEAD.

## Open Questions

- Should `mutate` take the mutation as a patch file, a sed expression, or a
  declared target+value? A patch file is the most general and the most auditable;
  decide at refinement.
- Does this belong in `tools/` (project) or in the YourTeam skill's `scripts/`
  (generic, reusable across projects)? The checks are project-generic in principle,
  but `mutate` needs the project's test selector syntax. Likely: generic core in
  the skill, project selector in config. Resolve before the estimate.

## History
- 2026-08-01: drafted alongside the checklist collapse that removed ~85 lines of
  prose covering A1/A1-ref/A3/A4/A7/A9. The collapse kept the rule; this story
  moves its mechanical half to the rung six retros said it belonged on. DRAFT —
  needs refinement and an estimate before it may enter a sprint.
