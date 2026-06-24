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
Add a repo-root `.gitattributes` that normalizes tracked text files to **LF in the
repository** (`* text=auto eol=lf`) so the LF→CRLF warnings stop and line endings are
consistent across platforms. Declare the repo's binary types explicitly (`binary`) so they
are never touched: images (`*.png`, `*.jpg`, `*.jpeg`, `*.gif`, `*.ico`), `*.pdf`, and
fonts (`*.woff`, `*.woff2`). Refined 2026-06-24: no tracked file needs to keep CRLF, so a
single `eol=lf` rule plus the binary exceptions covers the repo.

## Acceptance Criteria
- [ ] AC1: A `.gitattributes` exists at the repo root with `* text=auto eol=lf` and explicit
      `binary` rules for the image/pdf/font types listed above.
- [ ] AC2: After `git add --renormalize .` and committing, a subsequent edit-and-commit of a
      text file produces **no** `LF will be replaced by CRLF` warning.
- [ ] AC3: The four DoD commands (`pytest`, `lint-imports`, `scripts/check_fk_direction.py`,
      `alembic upgrade head`) remain green — this is a non-functional change.

## Open Questions
_(none — ready)_

## History
- 2026-06-24: created from Sprint 1 retro. Status: draft.
- 2026-06-24: refined with PO. Decision: single `eol=lf` rule, no file keeps CRLF; binary
  exceptions enumerated for the repo's actual binary types. Estimate held at 1. Status:
  ready. Planned into Sprint 2.
