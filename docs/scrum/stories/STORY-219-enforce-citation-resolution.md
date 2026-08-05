---
id: STORY-219
title: Wire tools/citation_sweep.py into the gate — the capability exists and is unenforced
type: chore
points: null
status: draft
filed: 2026-08-05
sprint: null
---

## Context

**Sprint 68 produced FIVE occurrences of one defect: a `file:line` citation made false by a commit
that never touched the cited content.** They are catalogued in that sprint's board under
`retro_candidates: RC-2`. This story is the mechanical remedy that evidence points at; the
process amendment itself is the retro's call, not this story's.

`tools/citation_sweep.py` already exists, already **resolves** citations against the files they
point into, and reports **126 failures across the 16 wiki articles** at the time of filing. It is
run by hand, occasionally, and enforces nothing.

## Why resolution, and not the staleness sweep

`yt_wiki.py` computes staleness as git arithmetic: `git diff <verified_sha>..HEAD -- <code_refs>`.
That answers *"might this article be out of date?"* — never *"is this claim true?"* Measured against
the five occurrences:

| # | What happened | `--range` staleness sweep |
| --- | --- | --- |
| i | STORY-204: prose landed two commits after its code | catches |
| ii | STORY-203: same | catches |
| iii | STORY-215 `7fb87fe`: `verified_sha` bumped over a Fact not re-read | **misses** |
| iv | STORY-203 `1d43b1b`: stamp over Facts displaced by its own import line | **misses** |
| v | `config-layer.md:264` + `config.py:316` citing `seed_topology.py:44` | **misses** |

Occurrence (v) is decisive: `scripts/seed_topology.py` is **not in `config-layer.md`'s `code_refs`**,
so no staleness check can ever flag that article however wrong the citation becomes — and the second
site, `backend/src/composition/config.py:316`, is a **source-code docstring** that no wiki tooling
covers at all. Only resolution catches all five.

**A `verified_sha` bump is a claim about what a human or agent re-read. No arithmetic can audit it.**
That is the gap; (iii) and (iv) are both instances of it, and in both the arithmetic was correct
while the claim was false.

## The known obstacle — size it honestly, do not let it become the reason to do nothing

The tool's 126 current failures are **mostly its own false positives**, by its own documented
limitations: bare-filename mentions (`decide.py` with no path) and content-anchor heuristics. The
distribution at filing: `demo-engine.md` 73, `core-pipeline-and-availability.md` 17,
`zone-rules.md` 28, the rest in ones and twos, with 6 articles already at zero.

So this cannot simply be added to the DoD gate today — it would be red on arrival. Refinement must
choose a shape. Options worth weighing:

1. **Ratchet**: fail only on an *increase* over a committed baseline count per article. Cheap,
   immediately enforceable, and stops new drift — which is the whole of what sprint 68 suffered.
2. **Tighten the tool first**, then enforce absolutely. Higher cost, better end state; risks the
   backlog becoming the reason enforcement never lands.
3. **Enforce only on citations carrying a line number** (`file.py:NN`), which is the failing class
   in all five occurrences, and treat bare filenames as advisory.

(3) then (1) is the likely cheapest correct path, but that is refinement's call, not this story's.

## Known-real failures to fix while here

Not false positives — verified stale at filing, and deliberately **not** fixed by STORY-215's fix
round so they would not be half-done:

- `docs/scrum/wiki/config-layer.md` — `backend/src/composition/seed_dynamo.py:56` (real: `:60`) and
  `backend/src/composition/vendor_health.py:97` (real: `:106`). Both drifted under STORY-204 and
  STORY-205, *before* sprint 68 opened; `config-layer.md`'s History records them.

## Not in scope

The retro amendment routing C3 down the enforcement ladder (RC-2 — the retro's call). Re-auditing
every wiki Fact. Widening the ZR-3 duplicate sweep.

---

## Planning re-check, 2026-08-05 (sprint-69 planning) — **estimate 3, NOT in sprint 69**

**Re-measured at HEAD, per article** (`tools/citation_sweep.py <article> .`, all 16):

| article | fails | | article | fails |
| --- | ---: | --- | --- | ---: |
| demo-engine.md | 73 | | dynatrace-adapter.md | 2 |
| zone-rules.md | 28 | | canonical-types-and-ports.md | 1 |
| core-pipeline-and-availability.md | 17 | | config-layer.md | 1 |
| ingest-service-and-pull-loop.md | 1 | | persistence-adapters.md | 1 |
| **the other eight articles** | **0** | | **TOTAL** | **124** |

Down from the 126 at filing, and the shape is as filed: **three articles hold 118 of the 124**, and
eight are already at zero. That distribution is what makes option (1)'s per-article ratchet cheap —
eight articles can be pinned at absolute zero immediately, and only three carry a nonzero baseline.

The retro's A18 landed the **staleness** half of C3 (`yt_wiki.py c3 --range`) and measured its
limits: advisory, and blind to occurrences (iii), (iv) and (v) in the table above. This story is the
resolution half, which is the half that reaches them. **A18 does not supersede it.**

**Sized 3**, on the (3)-then-(1) path this story already names as likely: enforce on
line-numbered citations, treat bare filenames as advisory, ratchet per article against a committed
baseline — plus the two known-real `config-layer.md` fixes. The residual risk is that tightening
the tool's anchor heuristics turns out to be needed to make even the line-numbered class
enforceable; if it does, that is a split, not a scope creep, and this story says so up front.

Deliberately NOT pulled into sprint 69: it is a tooling/enforcement story against the wiki, not an
audit-closure guard, and sprint 69 is already at its committed size. It is the strongest candidate
for sprint 70's first slot — sprint 68 produced five occurrences of the defect it prevents.
