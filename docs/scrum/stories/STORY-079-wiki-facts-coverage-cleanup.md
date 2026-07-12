---
id: STORY-079
title: Wiki Facts-coverage cleanup — every cited file covered by code_refs
type: chore
---

## Context
The YourTeam v2 Facts-coverage lint (`yt_wiki.py facts`, mechanizing the 2026-06-25 agreement)
found ~20 Facts across 8 articles citing repo files not covered by their article's `code_refs`
— the exact gap class that let `migrations-and-db.md` drift undetected from sprint 30 to 43
(the staleness sweep can never flag a Fact whose file isn't in `code_refs`). First run
2026-07-12 on the v2 branch; findings include test files (`backend/tests/fakes.py`,
`conftest.py`, endpoint tests), shared config (`pyproject.toml`, `CLAUDE.md`), and frontend
files cited by `frontend-zone.md` / `sample-mode.md`.

## Description
For each finding: either extend the article's `code_refs` with the cited file (only where it is
a DEFINING file for the article's subject — do not over-broaden; the 2026-06-25 scoping rule
stands) or re-home/split the Fact to an article that covers it. Knowledge content is
behavior-frozen: citations and refs move; claims do not change.

## Acceptance Criteria
- [ ] AC1: `python .claude/skills/yourteam/scripts/yt_wiki.py facts` exits 0 — zero uncovered
      Fact citations across all live articles.
- [ ] AC2: `yt_wiki.py` (sweep + facts + links) exits 0; every touched article is re-verified
      with `verified_sha` bumped to the current HEAD and a History line noting the coverage fix.
- [ ] AC3: No Fact's claim text changes (citation/ref re-homing only) — verifiable from the
      diff; `code_refs` extensions are limited to files the article's Facts actually cite.
- [ ] Six-gate DoD green (prose-only story; the gates prove no code was touched).

## Open Questions
<!-- none -->

## History
- 2026-07-12: filed and refined during pilot sprint 44 planning (v2 lint's first run); estimate 2;
  status ready under the PO's "run the pilot" directive.
