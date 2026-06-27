# Sprint 11 — Retrospective (2026-06-27)

**Outcome:** committed 4 (deliberate under-commit), accepted 4/4. The ruff DoD gate is live (the gate
is now six commands); the carried review chores are cleared.

## What went well
- **Ruff landed cleanly and safely.** The one-pass reformat was verified formatting-only — including the
  scary 129-line migration diff (exploded `sa.Column(...)` + quotes, zero DDL change). All six gates
  green.
- **Sequencing paid off.** Putting STORY-033 first meant the chores' cosmetic ACs (import order, trailing
  blanks) were auto-subsumed by the formatter — the plan's overlap note held exactly.
- **The conventions checklist (sprint-10 amendment) worked** — the plan carried it; nothing regressed on
  docstrings/patterns this sprint.

## What dragged
- **The reformat mass-stale'd the wiki.** A tree-wide `ruff format` touched files referenced by 7
  articles, drifting ~54 `file:line` citations (Facts still true — only pointers moved). The plan
  anticipated the chore-AC overlap but NOT the wiki-citation blast radius. This is a one-time cost of
  introducing a formatter against a line-pinned wiki, but it exposed that **line-pinned citations are
  brittle to formatting** — they'd re-drift on every future format/refactor.

## Amendment (PO-approved)
1. **Wiki Facts cite SYMBOLS, not bare line numbers** (`` `file.py::Symbol` `` / `` `file.py` ("section") ``).
   Symbol addresses survive formatting and most refactors; bare line numbers rot. The staleness
   mechanism is unchanged — only how a Fact *addresses* its evidence — so a formatting-only diff no
   longer invalidates the address. → working-agreements.md 2026-06-27; joins the plan.md conventions
   checklist. Rather than hand-patch 54 brittle line refs, the 7 affected articles were marked `stale`
   (honest/quarantined) and will be rehabbed under this policy by STORY-034.

## Follow-up filed
- **STORY-034** (2 pts, ready) — rehabilitate the 7 reformat-stale wiki articles with symbol-based
  citations (syntax `file.py::Symbol` resolved at retro), flipping each back to `verified`.

## Process metrics
- Stories: 3 committed / 3 done / 3 accepted. Blocked: 0. Hotfixes: 0. Fix loops: 0.
- Estimate accuracy: 3/3. Deliberate under-commit (4 of 6) — PO choice; honored.
- Wiki: 2 articles re-verified + re-stamped to `48217d7`; 7 marked stale (reformat drift) → STORY-034.
  The DoD grew from four to six commands (STORY-033).
