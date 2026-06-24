---
id: STORY-018
title: Add .gitattributes to normalize line endings
type: chore
---

## Context
From the Sprint 1 retro. Every commit on this Windows checkout emits
`warning: LF will be replaced by CRLF` noise because there is no `.gitattributes`
declaring how text files are normalized. Cosmetic, but it clutters every commit.

## Description
Add a repo-root `.gitattributes` that normalizes line endings for tracked text files
(e.g. `* text=auto eol=lf` with sensible binary exceptions), so the LF→CRLF warnings stop
and line endings are consistent across platforms.

## Acceptance Criteria (draft — confirm at refinement)
- [ ] AC1: A `.gitattributes` exists at the repo root normalizing text files (LF in the
      repo), with binary types excluded.
- [ ] AC2: After `git add --renormalize .`, a fresh commit produces no LF→CRLF warning.
- [ ] AC3: The four DoD commands remain green (no functional change).

## Open Questions
- Confirm the exact attribute set and whether any files should keep CRLF at refinement.

## History
- 2026-06-24: created from Sprint 1 retro. Status: draft — refine before its sprint.
