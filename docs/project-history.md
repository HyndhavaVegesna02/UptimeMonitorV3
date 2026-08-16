# Project history — superseded decisions, kept so they aren't re-litigated

Moved out of `CLAUDE.md` on 2026-08-01. Nothing here is current guidance. It exists
because the code still carries the shape of these decisions, and because without a
written record the same questions get re-opened and re-argued.

**This is deliberately NOT a wiki article.** It has no `code_refs` and no
`verified_sha`, so `yt_wiki.py` does not sweep it. That is intentional and matches
the rule already applied to `docs/scrum/sprints/` — history describes the past, so
staleness arithmetic against HEAD is meaningless for it. Only `docs/scrum/wiki/`
holds living knowledge that must stay current.

Read this when a decision looks wrong and you are about to change it. Otherwise
don't — it is history, and it costs nothing while it sits here unread.

---

## The failure-mapping claim that used to be in CLAUDE.md

The "Two things to know" section used to state that `map_synthetic_status` RAISES on
everything except the healthy OR-rule, that `dispatch.py` then discards the whole
batch, and that `DOWN`/`DEGRADED` therefore cannot reach the pipeline at all.

**All three were true until sprint 65 and are now false.** STORY-190 made a bad row
cost only itself: it is quarantined via `RejectedObservationRepository`, the rest of
the batch ingests, and the watermark advances — where previously one unmappable row
stalled that signal permanently.

The current behaviour is stated positively in CLAUDE.md and should be read there.
This entry exists only so the old claim isn't reinstated from memory.

## Deploy targets: Railway + Vercel

The original deploy targets (dossier §3). STORY-089 moved everything to AWS ECS +
CloudFront. Two stale code comments still named them (`composition/run.py`,
`frontend/src/api/client.ts`); STORY-181 corrected both.

## Persistence: Neon Postgres + Alembic

The persistence layer until STORY-087 migrated everything to DynamoDB. Both are
retired. `sqlalchemy`/`psycopg` now appear only as *forbidden* modules in the
import-linter config — if you see them referenced, that is the ban, not a dependency.

## Design lineage

`DESIGN-linear.app.md` (repo root) guided the sprint-25 shell. Sprint 38 retuned the
palette and type-scale values to an imported *Operator Dashboard* mock while keeping
that shape (7-status health palette, four shared primitives). The current reference
is the PO-built UI described in CLAUDE.md. The file stays on disk because sprint
history cites it.

## Three rejected UI attempts

Sprints 59 and 60 were rejected by the PO; sprint 61 was aborted. All three remain
unmerged on their branches.

That history is *why* frontend work now leads with a styleguide + shell checkpoint
instead of building six pages first, and why the design reference is a UI the PO
built themselves. This is the one entry here with live consequences for how a
frontend sprint is planned.

Note for anyone reading `velocity.json`: these three sprints are **absent** from it,
because only accepted sprints are recorded. The file therefore shows a 100%
acceptance rate that the actual history does not support. See STORY-211.

## `sample_mode`

The pre-demo-engine way to fake vendor data — it flipped already-normalized rows.
It went inert when the Dynatrace trial expired (2026-07-28), for the same reason
the trial matters everywhere else: no observations arrived to flip — and was
REMOVED by STORY-155a (frontend, sprint 73) and STORY-155b (backend, sprint 73).
See `docs/scrum/wiki/archive/sample-mode.md` for its history.

## `api/v1/_shared/middleware.py` and CORS

The docstring used to name STORY-017 as its intended CORS occupant. STORY-017 is
archived and was about deployment topology, not CORS. STORY-181 corrected the
docstring to state directly that no CORS is required — dev goes through the Vite
proxy, production is same-origin behind CloudFront — and left the file as a
documented seam for future middleware (e.g. authentication, still unassigned).

## The first frontend attempt

Sprints 23–24, built to a since-removed `DESIGN-airtable.md`, fully reverted in
`521764c`. Nothing in `frontend/` descends from it. See
`docs/scrum/wiki/frontend-zone.md`.
