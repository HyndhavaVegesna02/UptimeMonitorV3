# Sprint 2 — Retrospective

**Date:** 2026-06-24 · Process inspection, not product.

## Health metrics
- **Velocity 6/6 accepted** — third consecutive clean sprint (S0 8/8, S1 6/6, S2 6/6).
- Estimates accurate: STORY-006 (5) and STORY-018 (1) each completed in 1 attempt.
- Zero blocks, zero reviewer rejections, zero hotfixes. The full pipeline on STORY-006
  surfaced no critical/major findings — a signal the implementer brief carried enough spec
  to get it right first pass.

## What we inspected
1. **Repeated manual throwaway-Postgres setup (the real friction).** The migrated-DB dance
   was hand-rolled five separate times this sprint (STORY-006 implementer, spec reviewer,
   orchestrator DoD gate, STORY-018 implementer, its gate), each re-implementing
   `docker run` + wait + `alembic upgrade head` + the two-URL dialect split. Every remaining
   Zone 2–4 story is DB-heavy, so cost and foot-gun surface (wrong dialect; forgetting to
   migrate before the FK check) compound.
2. **STORY-018 met its AC but not its full intent.** AC2 (no `LF will be replaced by CRLF`)
   passed, but the warnings flipped to `CRLF will be replaced by LF` rather than vanishing —
   root cause is the contributor's global `core.autocrlf=true` at checkout, outside the
   story's scope. Repo *content* is now correctly LF; contributor-side noise persists.

## Amendments (PO decisions)
- **ADOPTED — Shared throwaway-DB harness.** Created **STORY-019** (chore, draft, provisional
  3 pts): a helper script + pytest session fixture that starts a throwaway Postgres, migrates
  it, and exports both URLs in their correct dialects, with CI/local reuse and
  teardown-on-failure. Working agreement added (2026-06-24): once STORY-019 lands, DB-gated
  work uses the shared harness instead of hand-rolling containers. Planning should consider
  sequencing STORY-019 before STORY-007 in Sprint 3 so the repository adapters' integration
  tests are written against the fixture from the start.
- **NOT ADOPTED — contributor `core.autocrlf` guidance.** Observation recorded here; no rule
  or chore created. The line-ending warnings now appear in the reverse (harmless) direction;
  repo content is LF-correct via `.gitattributes`.

## Wiki drift
- No stale articles. Two articles updated and re-stamped to the merge commit (`37458b8`):
  `migrations-and-db.md` (spine schema), `dev-setup-and-dod.md` (line-ending gotcha).
  `architecture-boundary.md` and `canonical-types-and-ports.md` verified-current at `ac1d468`.
  No article is stale ≥3 sprints. Link-lint clean.

## Carry-forward
- STORY-007 (repository adapters, 3 pts, ready) → Sprint 3, against the now-accepted spine.
- STORY-019 (DB harness, draft) → refine + estimate; consider before STORY-007.
