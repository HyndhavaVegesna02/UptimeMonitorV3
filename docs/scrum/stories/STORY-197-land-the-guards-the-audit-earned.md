---
id: STORY-197
title: Land the mechanical guards the audit earned, and adjudicate every rule
type: chore
points: 3
status: ready
refined: 2026-07-31
---

## Context

The sprint's whole point. A findings report is a document; a contract is a build failure. The PO's
framing was explicit — the audit's deliverable is *findings **plus mechanical guards***, with outcomes
routed **down** the enforcement ladder (memory `code-boundary-discipline`: "a ninth import-linter
contract beats another prose paragraph"). Sprint 65's retro (A9/A10) reinforced the same direction.

This story is scoped by what STORY-195 and STORY-196 actually find, which is not knowable at planning.
It is therefore **bounded, not open-ended** (AC5): the two highest-severity guardable findings get
guards here; everything else is filed with its guard sketch. A story whose size depends on a discovery
must have its own stopping rule written down, or it eats the sprint.

## Description

For the rules STORY-194 marked `GUARDABLE` and STORY-195/196 showed to matter, land real guards:

- preferred rung: a new `[[tool.importlinter.contracts]]` entry in `pyproject.toml` — it runs inside
  the DoD's existing import-boundary command, so it costs no new gate command;
- otherwise: a `pytest` test (this is the only available rung for anything `lint-imports` structurally
  cannot see — notably the `tools/` ↔ `src/` boundary, which lies outside `root_package = "src"`, and
  any rule about vendor vocabulary rather than import direction);
- **no new DoD gate command.** Adding a ninth command changes `.scrum/definition-of-done.md`'s
  contract and needs its own PO decision; if a rule can only be guarded that way, file it, don't
  smuggle it in.

Then close the loop: every rule in `zone-rules.md` ends the sprint adjudicated, so the catalogue is a
live scoreboard rather than a wish list.

## Acceptance Criteria

- [ ] **AC1** — At least one new mechanical guard lands for a rule the catalogue marked `GUARDABLE`,
      as either a new import-linter contract or a pytest test, and it runs inside the **existing** eight
      DoD commands — no new gate command is added.
- [ ] **AC2** — Every new guard is **SHOWN FAILING** before it is trusted (A7 + A9): either against the
      real violation it was written for, or — where the tree is already clean — against a deliberate
      mutation that introduces the violation and is then reverted. The story records, verbatim, the
      command, its RED output naming the guard, and the revert. **A guard that has only ever been green
      is not accepted**, and per A9 a spec reviewer who cannot answer "would this go red if I broke the
      guarded behaviour?" returns `NOT_MET`, not `MET`-with-a-note.
- [ ] **AC3** — The guard is asserted against the *rule*, not against today's file list: a test that
      enumerates the current modules and asserts that exact set passes today and never fails again.
      Where a guard must name modules (as `independence` contracts do), the story states what a future
      author must also update, and that instruction lands next to the contract as a comment.
- [ ] **AC4** — Every place stating the contract count is updated in the same commit: `CLAUDE.md`
      ("eight contracts", twice — the zones section and the DoD section), `.scrum/definition-of-done.md`,
      and any wiki article repeating the figure. `grep -rn` output for the figure is recorded **before
      and after**, so the sweep is auditable rather than claimed.
- [ ] **AC5** — Scope bound, stated as a result not an intention: guards land for at most the **two**
      highest-severity guardable findings. Every other guardable rule is filed as its own `draft`
      backlog story carrying the guard sketch (rung + assertion shape), and the story names which were
      deferred and why.
- [ ] **AC6** — Every rule in `docs/scrum/wiki/zone-rules.md` carries a final verdict of exactly one of
      `ENFORCED-BY <contract-or-test>` / `GUARDABLE-DEFERRED (<story-id>)` / `UNGUARDABLE (<why>)`.
      No rule is left un-adjudicated. The article's `verified_sha` is re-stamped only after its Facts
      are actually re-read against the code — a re-stamp without a read is what the wiki protocol
      forbids outright.
- [ ] **AC7** — The **full** 8/8 DoD gate is green on the final HEAD (not a `--only` subset — STORY-178
      means a `--only` that matches nothing exits 0, the one known false-green on the floor), with
      pass/skip counts recorded and skips at zero.

## Open Questions

None. What gets guarded is decided from STORY-195/196's severities in-process, under the PO's
2026-07-31 autonomy directive.

## History

- 2026-07-31: drafted and refined in sprint-66 planning. 3 points: writing a contract is small, but
  proving it RED (including mutate-and-revert on a clean tree) plus the count-consistency sweep plus
  adjudicating every catalogue rule is the bulk of it.
