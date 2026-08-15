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

**The split axis is consumer-then-producer.** ⚠ *The reason stated at planning was WRONG and is
corrected here.* I claimed removing the backend first would leave the SPA "calling a 404" in a broken
state. Verification refuted that: the SPA **degrades gracefully** — `client.ts:73-79` throws
`ApiError(status=404)`, `TopBar.tsx:52-58` renders *"Sample mode unavailable — retry"* instead of the
switch, and `TopBar.test.tsx:126` already tests exactly that path.

**The order still stands, for a better reason:** this story's diff **stales `sample-mode.md`** — nine
of that article's `code_refs` are files this story deletes or edits — and STORY-155b archives it.
Consumer-first archives the article **once**, instead of updating it and then archiving it.

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

## ⚠ This story WILL stale `sample-mode.md`, and that is expected — not a failure

`docs/scrum/wiki/sample-mode.md` is `tier: map` / `status: verified` and actively swept. **Nine of
its `code_refs` are files this story deletes or edits**: `api/types.ts`, `api/client.ts`,
`mocks/handlers/sampleMode.ts`, `mocks/handlers/index.ts`, `features/dashboard/useSampleMode.ts`,
`AppShell.tsx`, `nav/TopBar.tsx`, `nav/SampleModeBanner.tsx`, `pages/DashboardPage.tsx`. The sweep
(`yt_wiki.py:201-224`) diffs `code_refs` since the article's own last commit, and a deletion is not
whitespace — so it **will** report `sample-mode.md: STALE`.

**The resolution, decided at verification: demote it to `status: stale` with a reason pointing at
STORY-155b, which archives it.** This is the protocol's designed safe state (a stale article is
quarantined, never trusted-and-wrong) and is exactly what `frontend-zone.md` already does. Do **not**
re-verify its Facts — half its subject is about to be deleted, and a re-verification claim made a day
before the archive would be a false claim.

*(As drafted, this story's "Not in scope" forbade touching the article while AC6 required taking the
sweep's answer and `.scrum/definition-of-done.md:133-136` required acting on it — three rules and no
legal move. That contradiction is resolved by this section.)*

## Frontend surface, measured at planning, CORRECTED at verification (16 files)

**Delete outright:** `features/dashboard/useSampleMode.ts` + `.test.tsx` ·
`mocks/handlers/sampleMode.ts` · `nav/SampleModeBanner.tsx` + `.test.tsx` +
**`nav/SampleModeBanner.css`** (5 rules, imported at `SampleModeBanner.tsx:3` — missed at planning)

**Edit (seam removal):** `AppShell.tsx` · `nav/TopBar.tsx` + `TopBar.test.tsx` ·
`api/client.ts` + `client.test.ts` · `api/types.ts` · `mocks/handlers/index.ts` ·
`features/maintenance/useMaintenance.ts` + `.test.tsx` · **`AppShell.test.tsx`** (4 live sample-mode
tests at `:166, :172, :182, :190` — missed at planning) · **`tools/ui-sweep/sweep.mjs:194-231`**
(the `sample-on`/`sample-off` steps drive `button[aria-label="Sample mode"]`, which this story
deletes; it is outside `frontend/src` so no grep here would have caught it)

`putJson` (`client.ts:118`) has exactly **one** caller — the sample-mode PUT at `:254` — so it is
safe to delete with the feature. `frontend-zone.md:138` already records this.

`useMaintenance` is the surprise in that list — confirm what it actually uses before assuming it is
a stray import.

## Acceptance Criteria

- [ ] **AC1 (the banner and its trigger are gone from the UI)** — no sample-mode banner renders and
      no trigger is reachable. A test asserts the shell renders without them; the deleted
      components' tests are deleted with them, not left skipped.
- [ ] **AC2 (no frontend code path calls the sample-mode endpoint)** —
      `grep -riE "samplemode|sample_mode|sample-mode|sample mode" frontend/src` returns **zero**.
      ⚠ **The underscore-only pattern drafted at planning was holed** and would have passed while
      leaving live code behind: `AppShell.test.tsx` (4 tests) and `nav/SampleModeBanner.css` use the
      hyphen and space forms, and neither was in the original file list. The MSW handler is deleted
      and removed from `handlers/index.ts`, so nothing mocks a route the app no longer calls.
- [ ] **AC3 (`useMaintenance` is a PROSE edit, and the drafted binary was false)** — verification
      settled this: `useMaintenance.ts:20` and `:48` (and `useMaintenance.test.tsx:17`) reference
      `useSampleMode` **in docstrings only** — *"mirrors `useSampleMode`"*, *"the load+mutate shape
      `useSampleMode` established"*. There is **no import** (`useMaintenance.ts:1-5`). So the fix is
      to rewrite those comments, not to touch behaviour.
      ⚠ *The AC drafted at planning offered "stray import vs real behaviour, else stop and report" —
      a false binary that invited deleting through a doc comment. It is neither.*
- [ ] **AC4 (the backend is untouched)** — `git diff --stat` shows **no file under `backend/`**.
      That is STORY-155b's half; a mixed diff makes both halves harder to review and to revert.
- [ ] **AC5 (the test-count delta is accounted for exactly)** — state before/after and account for
      every lost test.
      ⚠ **The clause drafted at planning — "drops only by the deleted files' own tests" — was FALSE
      BY CONSTRUCTION and would have flagged its own correct outcome as a regression.** Counted at
      verification: roughly **18 of ~30** lost tests live in files that are *edited*, not deleted —
      `AppShell.test.tsx` (4, at `:166, :172, :182, :190`), `nav/TopBar.test.tsx` (7 of 8; only the
      `:42` theme-toggle survives), `api/client.test.ts` (2 describe blocks at `:343` and `:367`).
      The requirement is that the delta is **explained**, not that it is confined to deleted files.
- [ ] **AC6 (gate)** — the DoD commands the diff can affect exit 0 at the story's final HEAD, with
      counts recorded. **The gate is 9 commands as of sprint 72.** Run the wiki sweep after the last
      commit and take what it returns; do not pre-declare a blast radius.

## Not in scope

Any backend deletion (STORY-155b). **Archiving** `sample-mode.md` — that belongs with the backend
removal, because the article describes backend behaviour too and a tombstone written while half the
feature still exists would be false. **Demoting it to `status: stale` IS in scope and is required**
— see the staleness section above; that is the resolution of a contradiction this section previously
created. Repairing that article's mojibake (STORY-192).

## Open Questions

None.
