---
id: STORY-181
title: Retire stale references in code comments and docstrings (dead platforms, dead classes, dead story pointers)
type: chore
---

## Context

The PO-directed docs pass on 2026-07-29 (`e9a8ad3`) checked every claim in `CLAUDE.md`
against the repo and found ten wrong. Following its own `code_refs` turned up the same rot in
two wiki articles. **The production files were deliberately left alone** — editing them is a
story's job, not a docs pass's — so this story closes the remainder.

Twelve references across ten files. **No gate can catch any of them:** they are comments and
docstrings, so `pytest`, `ruff` and `lint-imports` stay green while the text misdirects every
reader who trusts it. Three of them name classes that **do not exist**, which is strictly worse
than vagueness — a reader greps for deleted code and concludes their checkout is broken.

## Description

Correct or delete each reference so it states current truth. Comments and docstrings only: no
behaviour change, no test edits, no file moves.

### The twelve sites

**(A) Dead deploy platforms** — STORY-089 moved everything to AWS ECS + CloudFront; Railway and
Vercel were never used.

| Site | Current text |
|---|---|
| `backend/src/composition/run.py:177` | "so production (Railway, no `.env` file present) is unaffected" |
| `frontend/src/api/client.ts:18-19` | "production (Vercel rewrites to the Railway backend — dossier §17…)" |

**(B) Retired persistence** — Neon Postgres + Alembic were retired by STORY-087. The first
three name **symbols that do not exist**: `grep -rn "class Postgres" backend/src` returns
nothing; every repository is `Dynamo*`.

| Site | Current text | Note |
|---|---|---|
| `backend/src/core/domain/component.py:17` | "both the fake and `PostgresComponentRepository` raise this identically" | phantom class |
| `backend/src/core/domain/publication.py:35` | "written once by `PostgresPublicationRepository.record`" | phantom class |
| `backend/src/core/ports/component_repository.py:53` | "The fake and `PostgresComponentRepository`…" | phantom class |
| `backend/src/adapters/persistence/__init__.py:1` | `"""adapters.persistence — repositories (e.g. neon)."""` | the exact wrong phrase `CLAUDE.md` carried until `e9a8ad3` |
| `backend/src/core/ports/__init__.py:7` | "a reader who has never heard of Dynatrace, Statuspage, or Neon must understand it" | the POINT of the sentence is vendor-blindness; swap the dead vendor for a live one |
| `backend/src/composition/run.py:4` | "constructs all live Postgres repository adapters" | |
| `frontend/src/features/maintenance/windowState.ts:8` | "the Postgres adapter's `starts_at <= at AND ends_at > at` agrees" | **the RULE is still correct** — only the adapter name is wrong. Keep the invariant, repoint the citation. |
| `pyproject.toml:50` | "Dossier §4 names vendor subpackages (inbound.dynatrace, outbound.statuspage, persistence.neon) that do not exist yet" | the comment explains why the contract lists real modules; only `persistence.neon` is dead |

**(C) Dead story pointers** — STORY-017 is `archived` and was titled *"Deployment topology"*. It
was never about CORS or authentication, so both comments send a reader to a story that cannot
deliver what they promise.

| Site | Current text | Truth |
|---|---|---|
| `backend/src/api/v1/_shared/middleware.py:4` | "Intended occupant: STORY-017 (CORS and authentication middleware)" | **No CORS is needed at all** — dev is same-origin via the Vite proxy, prod via CloudFront (STORY-089). The file contains only this docstring. |
| `frontend/src/api/actor.ts:3-5` | "Auth is deferred to STORY-017… When STORY-017 lands real operator identity" | Auth has **no queued story**. Say "unassigned" rather than naming a story that will never land it. |

### Explicitly NOT in scope

- `frontend/src/pages/MaintenancePage.tsx:104,118` — the `"e.g. Postgres upgrade"` placeholders
  are **user-facing copy**, and a Postgres upgrade is a perfectly good example of a maintenance
  window. Not stale; leave them.
- **Deleting `middleware.py`.** It is an empty seam cited by the 2026-07-10 proposal §6.2.
  Removing a documented architectural seam is a design decision, not comment hygiene — fix its
  docstring here and file a separate story if the seam should go.
- **Filing the auth story.** AC4 requires the comment to stop naming STORY-017; whether auth
  gets a story is a PO scope decision, not this story's to make.

## Acceptance Criteria

- [ ] **AC1 (dead platforms)** — Neither `Railway` nor `Vercel` appears anywhere under
      `backend/src/` or `frontend/src/`. Each of the two sites states the real topology (AWS ECS
      behind CloudFront, same-origin `/api/*`) or drops the platform mention entirely where it
      adds nothing.
- [ ] **AC2 (phantom classes)** — No comment or docstring under `backend/src/` names a
      `Postgres*` class. Each of the three sites either names the real `Dynamo*` repository or
      restates its point without a class name. The *claim* each one makes (fake-and-real agree on
      this error; the publication read model is written once) is preserved — this is a citation
      fix, not a deletion of the invariant.
- [ ] **AC3 (remaining retired-persistence prose)** — The five remaining sites in (B) are
      corrected. `ports/__init__.py:7` keeps its vendor-blindness point with a live vendor named
      in place of Neon. `windowState.ts:8` keeps the `starts_at <= at AND ends_at > at` invariant
      and repoints only the adapter name.
- [ ] **AC4 (dead story pointers)** — Neither `middleware.py` nor `actor.ts` names STORY-017.
      `middleware.py`'s docstring states that no CORS is required (dev: Vite proxy; prod:
      same-origin behind CloudFront) so a future reader does not implement it needlessly.
      `actor.ts` states that real operator identity is unassigned, and keeps its existing and
      still-true point that this function is the single swap-point.
- [ ] **AC5 (comment-only diff, proven mechanically)** — The story's diff over `backend/src/`,
      `frontend/src/` and `pyproject.toml` touches **only** comment, docstring and JSDoc lines.
      No executable line, no test file, and no `.scrum/` state changes. Evidence: the full
      `git diff` for the story reviewed line by line, with the count of changed non-comment lines
      stated as **zero**.
- [ ] **AC6 (the straggler check — a grep that must come back empty)** — The story records the
      output of a scan proving nothing survived:
      `Railway`, `Vercel`, `class Postgres`, `Postgres*Repository`, `Neon`, `STORY-017` under
      `backend/src/` + `frontend/src/`, plus `persistence.neon` in `pyproject.toml`. The only
      permitted hits are the two `MaintenancePage.tsx` placeholders named above. A story that
      fixes eleven of twelve sites and reports Done is the failure mode this AC exists to
      prevent — the count is mechanical, not judged.
- [ ] **AC7 (wiki + CLAUDE.md stay consistent)** — `docs/scrum/wiki/` and `CLAUDE.md` are checked
      for the same phrases; anything found is corrected in the same story. `e9a8ad3` cleaned the
      known ones, so this is expected to be a no-op — but "expected no-op, verified" and
      "not checked" are different states.
- [ ] **AC8** — All eight DoD gate commands exit 0, and the test count is **unchanged** from the
      story's start (a comment-only story that changes the test count did something else too).

## Open Questions

None.

## History

- 2026-07-29: filed out of the PO-directed docs accuracy pass (`e9a8ad3`), which corrected the
  same class of rot in `CLAUDE.md`, `docs/scrum/wiki/dev-setup-and-dod.md` and
  `docs/scrum/wiki/frontend-zone.md` and deliberately left production files untouched. Estimated
  2 points: the edits are trivial, but there are twelve of them across ten files in three zones
  plus `pyproject.toml`, and AC5/AC6 make the "did you get all of them" question mechanical
  rather than optimistic.
- 2026-07-29: pulled into sprint 63 alongside STORY-176 on PO instruction ("pull STORY-181 into
  sprint 63 with STORY-176").
