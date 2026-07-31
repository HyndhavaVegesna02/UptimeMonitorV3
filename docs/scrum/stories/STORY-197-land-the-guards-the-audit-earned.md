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

- 2026-07-31: drafted and refined in sprint-66 planning.
- 2026-07-31: implemented. Two guards landed, both **shown RED before being trusted** (C3/A9).
  The implementing agent was stopped mid-story by the PO after its three commits (`19fee13`,
  `e2fffae`, `0ba21d0`); it could not be resumed, so the orchestrator completed AC4–AC7 directly
  and **re-derived every RED proof itself** rather than accepting the agent's self-report.

### The guards

- **ZR-7** -> `backend/tests/test_zr7_pagination_guard.py` (2 tests). Every `.query(`/`.scan(` call
  site under `adapters/persistence/` must loop on `LastEvaluatedKey` or carry a named, reasoned
  exemption. Five exemptions are real unfixed findings, each citing **STORY-199**; one
  (`list_recent`) is permanent, because its port promises a stated bound rather than "all".
- **ZR-3** -> `backend/tests/test_zr3_duplicate_declarations.py` (2 tests). Promotes the committed
  `tools/zr3_duplicate_sweep.py` to a standing test; every collision must be adjudicated, and each
  unfixed entry cites **STORY-202**/**STORY-203**.

### Why these two, and not the other six (AC5's stopping rule, as a result)

ZR-3 and ZR-7 are the two highest-severity rules **with a live violation to prove the guard RED
against**. ZR-1/ZR-2/ZR-4 are clean (mutation-only proof, cheaper alongside their own stories);
ZR-5's real risk is cross-process and unguardable by a unit test; ZR-6 waits on STORY-200's design
decision; ZR-8 has two live violations, so a guard today would be RED on real code. Deferred guards
filed as **STORY-206..209**; full verdicts in `zone-rules.md`'s Adjudication table.

### The live-violation problem, and how it was resolved

Three of the strongest candidates had live violations. A zero-tolerance guard would have turned the
DoD gate RED and blocked every future story until the fix stories landed - which C4 forbids as a
side effect of a guard. Both guards therefore ship with **enumerated exemption/adjudication lists in
which every unfixed entry names its fix story**, so the guard is green today, fails loudly on any NEW
violation, and shrinks as fixes land. The per-entry fix-story citation is what stops an exemption
list becoming a permanent suppression list.

### RED proofs, re-derived by the orchestrator at acceptance

All four were run, observed RED, and reverted; the tree is clean and all 4 tests pass at HEAD.

1. **ZR-7, unexempted violation.** Removed the `is_under_maintenance` exemption ->
   `AssertionError: ZR-7 violation(s) ... dynamo_maintenance_repository.py:90
   [DynamoMaintenanceRepository.is_under_maintenance] does not loop on LastEvaluatedKey and has no
   exemption entry` -- `1 failed, 1 passed`. Reverted.
2. **ZR-7, stale exemption.** Added an exemption for `dynamo_observation_repository.py:113`, a call
   site that already loops -> `... :113 -- now loops on LastEvaluatedKey; remove this exemption, the
   fix has landed`. This is the branch that stops a landed fix leaving a rotting entry. Reverted.
3. **ZR-3, new collision.** Injected `FAKE_TABLE = "uptime-observations"` into
   `tools/demo_engine/store.py` -> `ZR-3 collision(s) found with no adjudication on record ... SRC:
   backend/src/composition/settings.py:21 [shape-ii Settings.dynamo_observations_table] TOOLS:
   tools/demo_engine/store.py:86`. Reverted.
4. **A negative result worth recording.** The same injection into `tools/citation_sweep.py` did
   **not** trip the guard. That is correct, not a hole: `_SELF_EXCLUDE_NAMES` skips the two sweep
   scripts, whose own literals are inherently noisy. Recorded because the first reading of a
   green result there looks exactly like a blind spot. **Noted for a future story:** the exclusion
   matches on BARE FILENAME, so any future `tools/**/citation_sweep.py` anywhere would also be
   skipped; a relative-path match would be tighter.

### AC4 - contract-count consistency (verification, not an edit)

Neither guard is an import-linter contract - both are pytest tests running inside the existing
`pytest` DoD command - so the contract count is **unchanged at eight** and no statement needed
editing. Verified rather than assumed, via `grep -rn` over `CLAUDE.md`, `.scrum/definition-of-done.md`
and `docs/scrum/wiki/`: every occurrence ("eight contracts" / "same 8 contracts" /
`Contracts: 8 kept, 0 broken`) is still accurate. **STORY-206 will take this to nine** and must
update all of them in its own commit.

### AC6 - every rule adjudicated

`zone-rules.md` gained an authoritative Adjudication table: ZR-3 and ZR-7 `ENFORCED-BY` their tests;
ZR-1/2/4/5/6/8 `GUARDABLE-DEFERRED` with a named story; ZR-5's operational half recorded
`UNGUARDABLE` with its reason. `verified_sha` re-stamped only after a real re-verification of the
article's citations - during which the committed `citation_sweep.py` reported **8 failures, all of
which proved FALSE on direct read** (two cite a memory file outside the repo; six fail the
content-anchor heuristic while the cited lines are exactly right). That limitation is now recorded in
the article itself, so a later story does not "fix" correct citations to satisfy a heuristic.
