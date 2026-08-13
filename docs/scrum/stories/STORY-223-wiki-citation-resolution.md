---
id: STORY-223
title: Wiki Fact citations that do not resolve from the repo root — 146 across 11 articles, silently skipped by the Facts lint
type: defect
points: null
status: draft
filed: 2026-08-13
sprint: null
---

## Context

Filed 2026-08-13 at the equilibrium refinement pass, from a live run of
`python .claude/skills/yourteam/scripts/yt_wiki.py`.

## The shape

**The same run prints both of these, and exits 0:**

```
== facts: CLEAN ==
...
TOTAL: 146 Fact citation(s) across 11 article(s) were never checked by the Facts lint.
A `facts: CLEAN` line does not cover them — that gap is what this check exists to make visible
```

The tool is **honest about it** — that second message was deliberately authored to make the gap
visible, and it works. But sprint-70's `review.md` and `retro.md` both recorded **"facts: CLEAN"
without the qualifier**.

That is sprint 70's dominant finding — *a claim in prose outruns the observation behind it* —
reproduced inside the wiki tooling's own reporting. It is why this is a story and not a note.

## Cause

Citations are written relative to a **source root** rather than the **repo root**:

- `composition/run.py` instead of `backend/src/composition/run.py`
- `api/client.ts` instead of `frontend/src/api/client.ts`

The Facts lint cannot resolve them, so it **skips** them rather than failing. Skipping is the right
default for an advisory check and the wrong one for a gate.

## Distribution (2026-08-13) — two articles are 64% of it

| Article | Unresolvable | Note |
| --- | --: | --- |
| `api-five-file-convention.md` | **59** | |
| `frontend-zone.md` | **35** | also `status: stale` |
| `sample-mode.md` | 13 | also 110 mojibake (STORY-192) |
| `ingest-service-and-pull-loop.md` | 9 | |
| `zone-rules.md` | 7 | **+ 16 bare `:NNN` with no filename at all** |
| `core-pipeline-and-availability.md` | 6 | also `status: stale` |
| `canonical-types-and-ports.md` | 5 | |
| `dynatrace-adapter.md` | 4 | |
| `statuspage-publish.md` | 4 | |
| `architecture-boundary.md` | 3 | |
| `demo-engine.md` | 1 | **+ 5 bare `:NNN`** |
| **TOTAL** | **146** | plus 21 bare line-only citations |

The bare `:NNN` citations are a **worse sub-class**: nothing anchors them at all, so no lint can
ever check them and they rot silently on the next edit above that line.

## *** Routing: the deliverable is a lint promoted from advisory to enforcing, not a prose pass ***

Wiki-protocol 2.3.0, routing row 1: *"Can this be a test, lint or gate command? Write the check.
Not the wiki."*

Fixing 146 citations by hand without closing the hole **reproduces the debt on the next article
written**. The repair is the cheap half; the enforcement is the story.

Expect a **per-article ratchet**, the way STORY-219 did it for the pytest-side citation gate — and
**reuse that machinery rather than building a second one**. Two citation gates with different
notions of "resolves" is a worse outcome than the current 146.

## Relationship to the filed content-anchor follow-up

This **is** the real size of the "content-anchor coverage" item filed at sprint-70 review (only 13
of 198 citations carry an excerpt anchor). Same defect family, three escalating steps:

1. **STORY-219 (done)** — enforced that a cited path resolves, for the pytest-side citation set.
2. **This story** — enforce that the *wiki's* paths resolve at all.
3. **Content anchors** — enforce that the cited line says what the Fact claims. Largest, and it
   depends on this one landing first: there is no point checking content at a path that does not
   resolve.

## Refinement must settle (this is what separates a ~3 from a ~8)

1. **The stale-article question.** Two of the eleven — `frontend-zone.md` (35) and
   `core-pipeline-and-availability.md` (6) — are `status: stale` and therefore **not swept**, so
   their 41 citations sit behind a quarantine. Either this story rehabilitates them, or the
   enforcing lint excludes stale articles until they are rehabilitated. **Do not rehabilitate
   `frontend-zone.md` by re-verifying 35 Facts as a side quest** — that is its own story, and
   re-verifying is what "touching a swept article" now means.
2. **Whether the fix is per-citation or per-article.** A repo-root prefix is mechanical for most,
   but some citations may name files that are simply gone — those are content decisions, not path
   decisions, and they must be separated before anyone starts editing.
3. **The bare `:NNN` sub-class** (21 of them, 16 in `zone-rules.md`). Decide whether they are in
   scope or a follow-up. They cannot be fixed by prefixing; each needs a human to identify the file.
4. **Where the enforcement lives** — `yt_wiki.py` (skill-level) or the repo's pytest citation gate
   (repo-level). This decides which of the 8 DoD commands catches a regression, and the two tools
   currently have different scopes.

## Not in scope

Content anchors (step 3 above). Repairing mojibake (STORY-192, though it overlaps in
`sample-mode.md` — coordinate). `deployment-and-infra.md`, the third stale article, is discharged
by STORY-222.
