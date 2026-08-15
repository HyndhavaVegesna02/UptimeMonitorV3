---
id: STORY-155a
title: Remove sample_mode from the frontend — the consumer goes first
type: chore
points: 3
status: ready
refined: 2026-08-15   # sprint-73 planning; split from STORY-155 (an 8) on measurement. PENDING PO lock.
sprint: null
---

## Why this is split from STORY-155, and why the frontend half goes FIRST

STORY-155 as filed is **an 8** — measured at sprint-73 planning, `sample_mode` spans **41 code
files across two toolchains** (27 backend, 14 frontend) plus a `tier: map` / `status: verified`
wiki article. The Definition of Ready forbids an 8 entering a sprint, so it is split.

**The split axis is consumer-then-producer, not backend/frontend for its own sake.** Removing the
backend endpoint first would leave the SPA calling a route that 404s — a broken intermediate state
on a branch that may sit unmerged for sprints. Removing the frontend first leaves an unused backend
endpoint, which is harmless. So this story lands first and STORY-155b follows.

## Context

`sample_mode` is the on-demand outage simulator (STORY-048), declared **TEMPORARY by PO directive
on 2026-07-03** and superseded by the Grail demo engine. `CLAUDE.md` records it as inert and names
STORY-155 as its removal.

**It is user-facing.** `AppShell.tsx:69` renders `<SampleModeBanner visible={bannerVisible} />` and
`TopBar` carries the trigger, so this is a visible change to the operator cockpit, not a dead-code
sweep.

## The removal recipe exists — and it has drifted, so verify it

`docs/scrum/wiki/sample-mode.md:226` holds a **complete mechanical deletion recipe** (STORY-048
AC7c), extended with the frontend surface. It is a genuine asset and should be followed.

**But it is not trustworthy on its own.** Checked at planning:

| Recipe claim | Reality |
| --- | --- |
| `adapters/persistence/sample_mode_repository.py` | **wrong** — the file is `dynamo_sample_mode_repository.py` (STORY-155b's problem, flagged here so both stories know) |
| `api/v1/sample_mode/` "all five files" | **correct** — 5 files, matching the five-file convention |
| every frontend path it names | **all exist** — verified one by one |

The article also carries **110 mojibake sequences** (measured 2026-08-15) — it is the single largest
contributor to STORY-192's 224. Archiving it here removes about half that story's scope.

## Frontend surface, measured at planning (14 files)

**Delete outright:** `features/dashboard/useSampleMode.ts` + `.test.tsx` ·
`mocks/handlers/sampleMode.ts` · `nav/SampleModeBanner.tsx` + `.test.tsx`

**Edit (seam removal):** `AppShell.tsx` · `nav/TopBar.tsx` + `TopBar.test.tsx` ·
`api/client.ts` + `client.test.ts` · `api/types.ts` · `mocks/handlers/index.ts` ·
`features/maintenance/useMaintenance.ts` + `.test.tsx`

`useMaintenance` is the surprise in that list — confirm what it actually uses before assuming it is
a stray import.

## Acceptance Criteria

- [ ] **AC1 (the banner and its trigger are gone from the UI)** — no sample-mode banner renders and
      no trigger is reachable. A test asserts the shell renders without them; the deleted
      components' tests are deleted with them, not left skipped.
- [ ] **AC2 (no frontend code path calls the sample-mode endpoint)** — `grep -ri "samplemode\|
      sample_mode" frontend/src` returns **zero** matches. The MSW handler is deleted and removed
      from `handlers/index.ts`, so nothing mocks a route the app no longer calls.
- [ ] **AC3 (`useMaintenance` is understood, not merely edited)** — state in the story what it used
      `sample_mode` for and why removing it is safe. If it turns out to carry real behaviour rather
      than a stray import, **stop and report** rather than deleting through it.
- [ ] **AC4 (the backend is untouched)** — `git diff --stat` shows **no file under `backend/`**.
      That is STORY-155b's half; a mixed diff makes both halves harder to review and to revert.
- [ ] **AC5 (nothing else regressed)** — the frontend test count drops only by the deleted files'
      own tests. State the before/after counts and account for the delta exactly; an unexplained
      drop means a test was removed that was covering something else.
- [ ] **AC6 (gate)** — the DoD commands the diff can affect exit 0 at the story's final HEAD, with
      counts recorded. **The gate is 9 commands as of sprint 72.** Run the wiki sweep after the last
      commit and take what it returns; do not pre-declare a blast radius.

## Not in scope

Any backend deletion (STORY-155b). Archiving `sample-mode.md` — that belongs with the backend
removal, because the article describes backend behaviour too and a tombstone written while half the
feature still exists would be false. Repairing that article's mojibake (STORY-192).

## Open Questions

None.
