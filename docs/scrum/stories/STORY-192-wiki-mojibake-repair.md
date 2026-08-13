---
id: STORY-192
title: Mojibake in docs/scrum/wiki/ — 218 corrupted sequences across 5 articles, and the encoding guard passes them clean
type: defect
points: null
status: draft
filed: 2026-07-30
sprint: null
---

## Context

Filed 2026-07-30 mid-sprint-65 during STORY-191's wiki update. **Re-measured and re-scoped
2026-08-13 at the equilibrium refinement pass** — the original measurement was stale, and the
wiki-protocol change (yourteam 2.3.0) added a constraint the story as filed would have violated.

This is the same defect class as STORY-188 (which repaired `.scrum/`, 12 sites across 5 files),
**one level up**: the wiki is the knowledge base every subagent dispatch reads.

## Current measurement (2026-08-13, re-derived)

| Article | Sequences | tier | status |
| --- | --: | --- | --- |
| `sample-mode.md` | **110** | map | **verified** |
| `ingest-service-and-pull-loop.md` | 57 | map | **verified** |
| `statuspage-publish.md` | 27 | map | **verified** |
| `deployment-and-infra.md` | 16 | map | stale |
| `deployment-topology.md` | 8 | **reference** | — (never swept) |
| ~~`dev-setup-and-dod.md`~~ | ~~30~~ | moved to `wiki/archive/` | |
| **TOTAL** | **218 across 5** | | |

The filing said 246 across 6. It reconciles exactly: **246 − 30 (archived) + 2 (ingest grew) = 218.**

## The corruption, and why the existing guard cannot see it

The bytes are the sequence `â€"` — a UTF-8 em-dash (`E2 80 94`) decoded as cp1252 and **re-encoded
as UTF-8**. So:

- The files are **valid UTF-8**.
- There is **no invalid byte** and **no U+FFFD** to detect.
- **STORY-188's guard (`test_scrum_encoding.py`) passes these files clean.**

A guard that passes corrupt content is the same failure class as a gate that greens having run
nothing — which is why this sits in the trust-the-floor tier rather than the cosmetic one.

## *** The constraint that resized this story: wiki-protocol 2.3.0 ***

The protocol now derives the staleness baseline from **the article's own last commit**, and says
so explicitly:

> *"an edit resets the baseline whether or not the Facts were re-read. So **editing a swept article
> IS re-verifying it** — if you are not re-verifying, do not touch it."*

**Three of the five files are `tier: map` + `status: verified`** (`sample-mode.md`,
`ingest-service-and-pull-loop.md`, `statuspage-publish.md`). A pure encoding repair would
**re-baseline all three without a single Fact being re-read**, silently converting "verified in
sprint-68" into "verified now."

That is precisely the failure mode 2.3.0's own text warns about, and it is sprint 70's dominant
finding — a claim outrunning the observation behind it — reappearing in a new place.

**Therefore this story repairs *and* genuinely re-verifies those three articles.** The other two
need no such care:

- `deployment-topology.md` is `tier: reference` — never swept, nothing to falsify.
- `deployment-and-infra.md` is already `stale` — no verification claim to break.

## Scope interactions (settle these before dispatch)

1. **STORY-222 tombstones `deployment-and-infra.md` and `deployment-topology.md`**, resolving 24 of
   the 218 as a side effect. **Sequence 222 first**, or accept the overlap — but do not let both
   stories edit the same two files.
2. **STORY-155 (remove sample_mode) is PO-deferred**, so `sample-mode.md` stays live and its 110
   sequences — **50% of this story** — stay in scope. Had 155 run, that article would have become a
   tombstone and half this story would have evaporated.
3. **`sample-mode.md` also carries 13 unresolvable Fact citations** (STORY-223). Re-verifying its
   Facts and fixing its citations are natural neighbours; decide whether to do both here or hand
   the citations to 223. Do not do half of each.
4. **The archived `dev-setup-and-dod.md`**: decide whether archived tombstones are in scope at all.
   The protocol treats `wiki/archive/` as history, and history is allowed to reference dead code —
   but it is not obviously allowed to be *unreadable*.

## Fix direction

- **Repair**: targeted replacement of the mojibake sequences. Mechanical, low risk.
- **Guard**: the existing encoding guard needs a **third check** — detect the classic
  cp1252-through-UTF-8 sequences — **generalised to cover `docs/scrum/` as well as `.scrum/`**.
  Per routing row 1 this is the load-bearing half: without it the corruption returns on the next
  article written.
- **Re-verify**: the three `verified` map articles, honestly, Fact by Fact.

## Refinement should settle

1. The exact sequence set to detect (em-dash is confirmed; check for the other common cp1252
   round-trips before pinning the guard, or it will need widening immediately).
2. Whether the guard lives with `test_scrum_encoding.py` or beside the wiki lints in `yt_wiki.py`.
   Note the wiki tool is skill-level and the encoding guard is repo-level — that boundary decides
   which gate command catches a regression.
3. **Re-measure before starting.** This measurement is from 2026-08-13; STORY-222 may have moved it.
4. The estimate. **Re-priced ~2 → ~4** at this pass: the repair is mechanical, the re-verification
   of three map articles is not.

## Not in scope

Rehabilitating `core-pipeline-and-availability.md` or `frontend-zone.md` (the other two stale
articles — they carry no mojibake and are STORY-223's and their own problem). Removing sample_mode.
