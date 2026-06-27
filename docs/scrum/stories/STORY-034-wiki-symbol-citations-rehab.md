---
id: STORY-034
title: Rehabilitate the 7 reformat-stale wiki articles with symbol-based citations
type: chore
---

## Context
Follow-up from Sprint 11 review/retro. STORY-033's one-pass `ruff format` + import-sort touched files
referenced by most wiki articles, drifting ~54 `file:line` Fact citations across 7 articles (mostly +1
from a ruff-inserted blank line after the module docstring; more under exploded multi-line calls). The
Facts remained TRUE — only the line pointers moved — so at the Sprint 11 compile pass the 7 affected
articles were marked `status: stale` (honest/quarantined) rather than hand-patched, because line-pinned
citations are brittle to formatting and would re-drift. This chore rehabilitates them under the
**symbol-based citation** policy adopted at the Sprint 11 retro (see working-agreements.md 2026-06-27).

The 7 stale articles: `architecture-boundary.md`, `canonical-types-and-ports.md`, `dynatrace-adapter.md`,
`ingest-service-and-pull-loop.md`, `migrations-and-db.md`, `persistence-adapters.md`,
`statuspage-publish.md`. (`core-pipeline-and-availability.md` and `dev-setup-and-dod.md` were re-pinned
in-sprint and stay `verified` — use them as the reference for the new citation style.)

## Acceptance Criteria (refined — PO-approved 2026-06-27)
- [ ] AC1: In each of the 7 stale articles, every Fact that pins a `file:line` is re-expressed per the
      retro's symbol-based citation policy (cite the defining symbol — `file::ClassName` /
      `file::function` / `file "section"` — rather than a bare line number, OR re-pin to the CURRENT
      correct line if the policy still allows line numbers for a specific case). Each Fact is verified
      against the current code at rehab time.
- [ ] AC2: Each rehabbed article's frontmatter flips `status: stale` → `status: verified` and bumps
      `verified_sha` to the current `main` HEAD at rehab time. No article is left stale.
- [ ] AC3: Internal `[[links]]` still resolve; no Fact cites a file outside the article's `code_refs`
      (the existing every-Fact-covered agreement).
- [ ] AC4: `pytest` + `lint-imports` + `ruff check` + `ruff format --check` green (doc-only change, but
      run the gate). No code under `src/` is touched.

## Resolved Questions
- **Symbol-citation syntax → `` `file.py::Symbol` ``** (e.g. `` `status.py::ComponentStatus` ``,
  `` `decide.py::DecideService.decide` ``), or `` `file.py` ("section") `` where no symbol applies, per
  the Sprint 11 retro amendment (working-agreements.md 2026-06-27). Apply uniformly across the 7 articles.

## History
- 2026-06-27: created from Sprint 11 review/retro (tree-wide reformat drifted ~54 line citations; 7
  articles marked stale rather than hand-patched). Estimate: 2 (7 articles, doc-only, mechanical).
- 2026-06-27 (retro): symbol-citation syntax resolved (`file.py::Symbol`). Status: draft → ready.
