---
id: STORY-216
title: Mechanise the ENFORCED-BY claim in zone-rules.md — a row may not claim a guard that does not exist
type: chore
points: 3
status: draft
filed: 2026-08-03
sprint: 69
---

> **REFINED at sprint-69 planning (2026-08-05).** Sized and shaped so the two-sprint audit-closure
> plan is credible; the AC below are a proposal, not yet PO-approved. **The open question is now
> settled — see "Where it lives, settled" below. Estimate confirmed at 3.**

## Context

Sprint 67's loudest finding (STORY-200, quality review, MAJOR-1). `docs/scrum/wiki/zone-rules.md`'s
adjudication table marked `ZR-6` as **`ENFORCED-BY`** a named test — and the claim was false. Proven
by mutation: reverting the *entire* ZR-6 fix left the suite at 696 passed, identical to HEAD. The
named test pinned a different property (a 2-member subset guard), not the one the row claimed.

The rule that should have caught it already existed, twelve lines above the offending row: the
table's own legend defines `ENFORCED-BY` as requiring a guard **"shown RED — never merely 'is
green'"**. `ZR-3` and `ZR-7` record their red demonstrations; `ZR-6`'s row recorded none, *and none
was possible*. The definition was right there and went unread.

The sprint-67 retro declined to write an amendment about it (agreement A15: a rule that exists and
was not followed is shortened or relocated, never restated more emphatically) and filed this story
instead — the lesson at the rung that can actually hold it.

## Why it runs LAST in sprint 69

STORY-206/207/208/209 flip four rows from `GUARDABLE-DEFERRED` to `ENFORCED-BY`. This guard checks
every such row, so it must run after they land — otherwise it validates a table that is about to
change four times.

## Proposed Acceptance Criteria

- [ ] **AC1 — the row grammar is SPECIFIED, not inferred.** This is the AC that plan verification
      rewrote; see "The grammar, and why it is an AC" below. The check's scope and parse rules are:
      - **Scope:** the single markdown table under the `## Adjudication` heading. `Detail`-column
        prose, the legend, the rule bodies and the `## History` section are **out of scope** — they
        carry `ENFORCED-BY` and bare filenames that are prose, not claims.
      - **Reference syntax:** a guard reference is a **backtick code span** inside the **Verdict**
        cell. `ENFORCED-BY` marks the *cell*, not each reference; a cell may carry **more than one**
        reference (ZR-8 carries four across two findings), and every one is checked.
      - **Two reference kinds:** a **path** (`backend/tests/x.py`, optionally `::test_name`) resolves
        against the filesystem; a token that is not a path resolves as an **import-linter contract
        name** against `pyproject.toml` (this kind exists for ZR-1 — see STORY-206 AC6, coordinated
        with this AC at plan verification).
      - **A cell may carry two verdicts.** `ENFORCED-BY` + `UNGUARDABLE` together is legal and ZR-5
        is the named case; the legend line claiming "exactly one verdict per rule"
        (`zone-rules.md:801`) is corrected by STORY-209, which already breaks it at `:812` today.
      - **Non-vacuity floor:** the check asserts all eight rule ids `ZR-1..ZR-8` were parsed **and**
        that at least one `ENFORCED-BY` reference was resolved. A zero-row parse — heading drift, a
        moved table — must go RED, never green. Without this the guard reproduces sprint-67's
        MAJOR-1 *inside the guard built to end it*.
- [ ] **AC2** — the named target is a real test, not merely a file: where a reference carries
      `::test_name`, the check AST-parses that file and asserts a `FunctionDef` of that name exists
      (no `pytest` subprocess — see "Where it lives, settled"), so a row cannot point at a module
      whose test was renamed away. **Residue, stated in the check's docstring and in its assertion
      failure message:** a test that exists but is skipped, xfailed or deselected still counts as
      present here.
- [ ] **AC3** — **the honest half.** "Has been shown RED" is prose in the Detail column; a test can
      check that the row *records* a red demonstration (a mutation named, with a command), but it
      cannot verify the demonstration happened. AC3 states that limit **in the check's docstring and
      in its assertion failure message** — corrected at plan verification: "in the check's output"
      was unimplementable, because a passing `pytest` emits nothing. Nobody may later read a green
      run as proof the mutations were real. A guard that overclaims here would be the very defect it
      exists to catch.
- [ ] **AC4 — shown RED three times, one per resolution path (A9).** Each mutation is applied to a
      copy of the table or to the real file and reverted, with `git diff` empty after each, all
      recorded verbatim in the board's `reality_gate` block:
      (a) point a row at a **nonexistent path** → fails naming the row;
      (b) point a row at an **existing path with a nonexistent `::test_name`** → fails naming the
      row (this is AC2's half, which the original AC4 left unproven);
      (c) point ZR-1's row at a **nonexistent import-linter contract name** → fails naming the row
      (AC1's second reference kind).
- [ ] **AC5** — it runs inside the existing eight DoD commands (a `backend/tests/` test), adding no
      ninth command.
- [ ] **AC6** — every row at HEAD passes, or a failing row is **fixed rather than exempted**. An
      exemption list on this particular guard would reproduce the original defect. **Read this
      together with AC1:** a "failing row" means one failing the specified grammar. Plan
      verification showed that four *correct* rows go red under a looser reading — and
      `zone-rules.md:860-862` already warns that "fixing" those would be corrupting correct
      citations to satisfy a heuristic. If the grammar and a correct row disagree, the grammar is
      wrong.

## The grammar, and why it is an AC (plan verification, 2026-08-05)

The first refinement pass left the row grammar to the implementer. Plan verification implemented
**five plausible literal readings** of that AC and ran each against the real table
(`zone-rules.md:806-815`). They disagree completely:

| Reading | Result at HEAD |
| --- | --- |
| **A** — `ENFORCED-BY` + next token, Verdict cell | **4 false REDs of 4** — captures the trailing backtick, so every path "does not exist" |
| **B** — same, backticks stripped | green, but finds **4 of the 6** guards claimed — ZR-8's ` + `-joined pair is silently skipped |
| **C** — every code span in an `ENFORCED-BY` Verdict cell | finds all 6, all resolve — **the correct grammar, and not what the AC said** |
| **D** — whole row incl. Detail | 4 false REDs, incl. a bare `test_approval.py::…` that is prose in ZR-6's Detail |
| **E** — whole file | pulls `ENFORCED-BY` from the legend and from History `:1292-1293`, where the token is line-wrapped away from its path — it resolves today only by luck |

Reading A plus AC6 ("a failing row is fixed, never exempted") sends a literal implementer to edit
**four correct rows** to satisfy a broken regex. AC1 now pins reading C.

## Where it lives, settled (refinement, 2026-08-05)

**`backend/tests/`, inside `pytest`** — as AC5 assumed. Three reasons, in order of weight:

1. **`yt_wiki.py` must stay project-GENERIC** (PO rule, 2026-07-13, binding). `zone-rules.md`'s
   adjudication table is a project-specific document with a project-specific format; a parser for
   it inside the shared skill script would violate that rule outright. This alone decides it.
2. **`yt_wiki.py` is not a DoD command.** It runs at standup and before dispatch. A check landed
   there gates nothing at story close; landed in `pytest` it inherits the strongest rung already
   present, at zero extra command cost (AC5).
3. **What it validates are backend tests and `pyproject.toml` contracts** — the objects live on the
   Python side of the repo, and so should the resolution logic.

Consequence for AC2: no `pytest --collect-only` subprocess (a pytest run inside a pytest run is
slow and recursion-prone). AST parse of the named file is enough to catch the failure this guard
exists for — a row pointing at a renamed-away test — and its residue is stated rather than hidden.

## Sequencing note

Runs LAST in sprint 69, after STORY-206/207/208/209 have each flipped a row into `ENFORCED-BY`.
Those four rows are this guard's first real inputs; AC6 (fix a failing row, never exempt it) is
therefore also a check on its four siblings' work.
