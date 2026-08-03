---
id: STORY-216
title: Mechanise the ENFORCED-BY claim in zone-rules.md — a row may not claim a guard that does not exist
type: chore
points: 3
status: draft
filed: 2026-08-03
sprint: 69
---

> **DRAFT — refined at sprint-69 planning.** Sized and shaped here so the two-sprint audit-closure
> plan is credible; the AC below are a proposal, not yet PO-approved.

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

- [ ] **AC1** — a test parses `zone-rules.md`'s adjudication table and asserts that every row whose
      verdict contains `ENFORCED-BY` names a path that **exists**. A row naming a deleted or renamed
      test file fails loudly.
- [ ] **AC2** — the named target is a real test, not merely a file: the named
      test/function is collected by `pytest` (e.g. via `--collect-only`), so a row cannot point at a
      module whose test was renamed away.
- [ ] **AC3** — **the honest half, and the one refinement must settle.** "Has been shown RED" is
      prose in the Detail column; a test can check that the row *records* a red demonstration
      (a mutation named, with a command), but it cannot verify the demonstration happened. AC3 states
      that limit **in the check's own output**, so nobody later reads a green run as proof the
      mutations were real. A guard that overclaims here would be the very defect it exists to catch.
- [ ] **AC4** — shown RED: point a row at a nonexistent guard; the check fails naming the row;
      restore; `git diff` empty.
- [ ] **AC5** — it runs inside the existing eight DoD commands (a `backend/tests/` test), adding no
      ninth command.
- [ ] **AC6** — every row at HEAD passes, or a failing row is **fixed rather than exempted**. An
      exemption list on this particular guard would reproduce the original defect.

## Open questions for refinement

- Does the check belong in `backend/tests/` (inside `pytest`, per AC5) or in
  `.claude/skills/yourteam/scripts/yt_wiki.py` (which already lints the wiki, and where amendment
  A16 landed)? The catalogue is a wiki article, but the guards it names are backend tests. Deciding
  this is refinement's job; AC5 assumes the former.
