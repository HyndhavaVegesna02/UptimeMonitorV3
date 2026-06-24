# Sprint 2 — Review

**Date:** 2026-06-24 · **Goal:** the eleven-table spine is migrated, reversible, and
FK-direction-clean — so repositories (Sprint 3) and every later zone have real tables to
attach to. **Goal met.**

**Committed 6 pts · accepted 6 pts (2/2 stories).** Branch `sprint-2` off tag
`sprint-2-start`. Merged to `main` on acceptance.

## STORY-006 — Spine schema migration (5 pts) — ACCEPTED
Migration `3a8254bcfe59_spine_schema.py` (`down_revision = eda70ac11454`) creates the full
§9 spine: topology (`apps` w/ `config jsonb NOT NULL`, `signals`, `components`), signals
(`observations`, `problem_signals`, `watermarks`, `rejected_observations`), workflow
(`status_proposals`, `approval_events`, `publications`, `maintenance_windows`).

- Spec review (Opus): **PASS** — all 6 AC MET, each verified against a live Postgres,
  including a functional proof of the one-active-proposal-per-component partial-unique index.
- Quality review (Opus): **APPROVE** — 0 critical, 0 major, 2 minor notes (recorded on story).
- DoD gate (orchestrator-run @ `cc54e13`): alembic head 0 · pytest 77 passed · lint-imports
  3 kept/0 broken · FK-direction 10 checked/0 violations.
- Within-AC implementer decisions endorsed by review: `health`/`status`/`state` as `text` +
  CHECK mirroring the closed Python enums (single source of truth, not Postgres ENUM);
  `rejected_observations.signal_key` deliberately unconstrained (a rejected row's key may not
  exist in topology — often the reason it was rejected); FKs `RESTRICT` into seeded topology,
  `CASCADE` from `approval_events`/`publications` into their owning proposal.

## STORY-018 — .gitattributes line-ending normalization (1 pt) — ACCEPTED
Repo-root `.gitattributes` (`* text=auto eol=lf` + binary rules). Stops the per-commit
`LF will be replaced by CRLF` warnings.
- Lite pipeline (1 pt): no reviewers; DoD gate only. All four gates exit 0 @ `69219ed`.
- Finding (not a defect): the index blobs were already LF, so `git add --renormalize .`
  staged nothing — the working-tree CRLF came from the contributor's global
  `core.autocrlf=true` at checkout, not from repo content. Captured in `dev-setup-and-dod.md`.

## Wiki compile pass (completed before review)
- `migrations-and-db.md` — spine schema folded in; `verified_sha` → `54eb5c5`.
- `dev-setup-and-dod.md` — line-ending gotcha + `.gitattributes` code_ref; `verified_sha` → `6128cb0`.
- Link-lint clean; `architecture-boundary.md` and `canonical-types-and-ports.md` verified-current.

## Outcome
Both accepted → merged to `main`. Velocity: 6 accepted (sprint 2). Zone 2 schema complete;
STORY-007 (repository adapters) carries forward to Sprint 3 against the now-accepted spine.
