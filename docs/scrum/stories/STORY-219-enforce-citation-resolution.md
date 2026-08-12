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

---

## Refinement, 2026-08-13 (sprint-70 planning) — **estimate 3 CONFIRMED, AC authored**

**Re-measured at sprint-70 HEAD (`a360e50`), all 17 articles: TOTAL 129, up from the 124 measured at
sprint-69 planning.** The rise is not new drift — it is the yourteam-2.3.0 wiki split. `zone-rules.md`
fell 28 → 18 and the new `zone-rules-history.md` carries 15, so the split moved citations rather than
resolving them, and added a handful.

| article | fails | | article | fails |
| --- | ---: | --- | --- | ---: |
| demo-engine.md | 73 | | dynatrace-adapter.md | 2 |
| zone-rules.md | 18 | | canonical-types-and-ports.md | 1 |
| core-pipeline-and-availability.md | 17 | | config-layer.md | 1 |
| **zone-rules-history.md** | **15** | | ingest-service-and-pull-loop.md | 1 |
| | | | persistence-adapters.md | 1 |
| **the other eight articles** | **0** | | **TOTAL** | **129** |

**Shape chosen: option (3) then option (1)** — enforce line-numbered citations, ratchet on a
per-article baseline. Four articles hold 123 of the 129; eight pin at absolute zero on day one.

**NEW QUESTION THIS MEASUREMENT RAISES, and AC6 settles it:** `zone-rules-history.md` is
`tier: reference`. Reference articles carry no `code_refs` and are never swept for staleness — that
exemption is what makes the tier honest. Whether they are also exempt from *citation resolution* is
a different question and has never been decided. It matters immediately: reference tier is where
this project puts its History sections, and 15 of the 129 are already there.

## Proposed Acceptance Criteria

**REWRITTEN 2026-08-13 after pre-lock plan verification returned GAPS.** The first draft's AC2
claimed that enforcing only line-numbered citations would quarantine the tool's three documented
false-positive classes. **That was false and is now corrected.** `tools/citation_sweep.py:41-44`
makes `:(\d+)` **mandatory** in `CITATION_RE`, so a citation without a line number is never extracted
at all. Measured: **129 of 129 failures carry a line number** — the filter removed nothing.

The verifier also established what this tool actually enforces, which is less than the story assumed:

- Measured failure causes: **file-missing 124, anchor-mismatch 5, line-count-short 0.**
- The 124 are bare filenames that DO carry line numbers (`server.py:66`, `harness.py:615`). "Bare
  filename" and "no line number" are orthogonal; the story had conflated them.
- Content is checked only where a parenthesized `` (`excerpt`) `` anchor exists — **8 of 195**
  distinct citations repo-wide. 58 more get a line-count-only check.
- **Decisive:** the story's own occurrence (v), `scripts/seed_topology.py:44`, is reported **OK**.
  So "only resolution catches all five" is false *for this tool*. A wrong-but-in-range line number
  passes.

**The story is therefore re-scoped, not re-priced.** It still buys a real floor — 124 unresolvable
paths is the dominant class and the one `yt_wiki.py`'s own citations note independently reports as
146 unchecked Facts — but it must say what it enforces. Content-anchor coverage is a separate,
larger question and is filed as a follow-up, not smuggled in here. **Estimate stays 3.**

- [x] **AC1 — enforcement runs inside `python -m pytest`, not as a ninth DoD command**, and STATES
      THE ENFORCED PROPERTY HONESTLY in the test's docstring: *the cited path resolves from the repo
      root, and the file is long enough to contain the cited line; the cited CONTENT is verified only
      for the minority of citations carrying a parenthesized excerpt anchor.* The docstring names the
      residual limit explicitly — **a wrong-but-in-range line number passes** — and cites
      `scripts/seed_topology.py:44` as the worked example that passes today. A docstring implying
      this check proves citations correct is not Done.
- [x] **AC2 — the enforced set is filtered on PATH RESOLVABILITY, not on line-number presence.**
      A citation whose path contains no `/` (a bare filename such as `server.py:66`) is reported in a
      separate advisory list; a citation with a repo-relative path is enforced. This is the filter
      that actually discriminates. The test asserts the two lists partition the extracted set, so a
      citation cannot fall out of both.
- [x] **AC3 — the baseline is committed DATA, not a number in prose**, one entry per article. **The
      glob is named literally in the baseline file**: `docs/scrum/wiki/*.md`, top level only, 17
      articles — `docs/scrum/wiki/archive/` is OUT of scope and the file says so, because AC4 makes an
      absent article fail and the two archived articles would otherwise be a silent 19-vs-17 ambiguity.
- [x] **AC4 — the ratchet only goes down.** A count BELOW its baseline fails with an instruction to
      lower the baseline in the same commit, so paid-down debt cannot silently refill. An article
      absent from the baseline file fails rather than defaulting to unlimited.
- [x] **AC5 — shown RED, with the near-miss control (A9).** (a) Add a citation using a FULL
      repo-relative path with a line number GREATER THAN THE FILE'S LENGTH to a zero-baseline article
      → RED. (b) Add one to a nonzero-baseline article, taking it above baseline → RED. (c) Delete a
      failing citation from a nonzero article without lowering the baseline → RED per AC4.
      **(d) THE CONTROL, which is what makes (a) meaningful:** a full-path citation with a
      wrong-but-IN-RANGE line number stays **GREEN**, and that green is recorded next to (a)'s red.
      Without (d), `settings.py:20` (correct) and `settings.py:99999` (wrong) both FAIL identically
      for the same irrelevant reason — the path — and (a) proves nothing.
- [x] **AC6 — `tier: reference` articles are EXEMPT, read mechanically from frontmatter.** This is
      not an open choice: `references/wiki-protocol.md:21` already defines reference tier as
      "append-only, cites no live line", and `:56` says an article that wants to cite code IS a map
      article. `zone-rules-history.md`'s 15 failures are citations INTO HISTORY — claims about past
      state, which a tool resolving against HEAD cannot judge. Worse, AC4's ratchet on an append-only
      article goes RED on the next appended entry, forcing its author to move a baseline they did not
      set — the shape this sprint's ordering exists to prevent. The exemption is read from the `tier:`
      field, never a hand-listed filename, and the reason is recorded in the baseline file header.
- [x] **AC7 — the two known-real drifts are corrected, WITHOUT any claim about the baseline.**
      `config-layer.md`'s `seed_dynamo.py:56` (real `:60`, `for sig in app.signals:`) and
      `vendor_health.py:97` (real `:106`, `for signal in app.signals:`). Both are genuinely stale and
      worth fixing. **Both report OK today** — `config-layer.md:271-272` uses an em-dash excerpt form
      that `CITATION_RE` does not read as an anchor — so fixing them moves the count by **zero**, and
      any AC requiring them to LOWER the baseline would be unsatisfiable. `config-layer.md`'s single
      real failure is `dispatch.py:44`, unrelated to either.
- [x] **AC8 — the 129 are not silently accepted, and a zero is not silently trusted.** The baseline
      file header states that a nonzero entry is unpaid debt and names the four articles holding 123
      of it. It ALSO distinguishes the two kinds of zero: **seven of the eight zero-pins have no
      extracted citations at all** (vacuously clean), and only `deployment-and-infra.md` (10
      citations, all passing) is genuinely clean. A baseline that reads as an approval, or that lets
      an empty article look like a verified one, is not Done.
- [x] **AC9** — full 8/8 DoD gate green at the final HEAD, including the new test.

## History

- sprint-70 (STORY-219): `tools/citation_gate.py` partitions `citation_sweep.py`'s extracted
  citations into ENFORCED (repo-relative path) vs ADVISORY (bare filename) -- the first draft's
  "filter on line-number presence" was a no-op (`CITATION_RE` mandates a line number; 129 of 129
  raw failures carried one) and was corrected during plan verification before this story opened.
  Re-measured at HEAD (`db76941`'s parent): raw sweep 129 (demo-engine.md 73, zone-rules.md 18,
  core-pipeline-and-availability.md 17, zone-rules-history.md 15, the rest in ones/twos, eight at
  zero) -- reconciled exactly against sprint-70 planning's own re-measurement. Of the 129, only 16
  are ENFORCED (path contains `/`): demo-engine.md 8, zone-rules.md 6, dynatrace-adapter.md 1,
  zone-rules-history.md 1 -- the last EXEMPT under AC6 (`tier: reference`, read live from
  frontmatter by `gate.article_tier`, never a hand-listed name), leaving a 15-total committed
  ratchet baseline across 14 map-tier articles (`backend/tests/test_citation_gate.py::BASELINE`).
  `test_ac4_ac6_enforced_citation_count_matches_baseline_exactly` is an EQUALITY ratchet -- above
  baseline is new drift, below is undeclared paid-down debt -- both fail, per AC4.
  AC5 shown RED (all reverted, `git diff` empty after each; full tails recorded outside the repo):
  (a) a full-path/out-of-range-line citation into `api-five-file-convention.md` (baseline 0) ->
  RED, `ABOVE baseline`, the ONLY thing in this evidence set that exercises `check_citation`'s
  line-count-short branch (zero real citations hit it today); (b) the same shape into
  `zone-rules.md` (baseline 6) -> RED, the SAME `ABOVE` branch as (a), at a nonzero starting
  baseline -- recorded as one branch proven at two starting conditions, not two independent
  proofs; (c) fixing `zone-rules.md`'s `composition/app.py:224` (both occurrences) without
  lowering its baseline -> RED, `BELOW baseline`, a genuinely distinct branch from (a)/(b); (d)
  the control -- a full-path, wrong-but-in-range-line citation into the SAME article as (a)
  (`api-five-file-convention.md`) -> stays GREEN, recorded side by side with (a)'s red.
  AC7: `config-layer.md`'s `seed_dynamo.py:56`/`vendor_health.py:97` corrected to the real
  `:60`/`:106` -- both reported OK before and after (line-count-only, no excerpt anchor), so
  enforced count for that article stays 0; confirmed by re-running the full test module.
  AC6 resolved by reading `tier:` from frontmatter mechanically at test time
  (`gate.article_tier`), cross-checked against the baseline's own descriptive `tier` field by
  `test_ac6_reference_tier_articles_are_read_from_frontmatter` -- exempts
  `api-five-file-history.md`, `deployment-topology.md`, `zone-rules-history.md` today, derived,
  not hand-listed.
  Incidental: `tools/citation_gate.py:53`'s `str.find("\n---", 3)` start-offset literal collided
  with `FreshnessConfig.stale_after_cycles=3` under ZR-3's sweep -- adjudicated INDEPENDENT in
  `backend/tests/test_zr3_duplicate_declarations.py`.
  DoD gate 8/8 at final HEAD: `python -m pytest` 761 passed / 0 skipped; import-linter 9 kept, 0
  broken; ruff check/format clean; cfn-lint exit 0; frontend `npm test` 363 passed, `npm run
  build`/`npm run lint` exit 0.

## Filed as follow-up, not done here

**Content-anchor coverage.** Only 8 of 195 citations carry the parenthesized excerpt this tool needs
to check content, which is why a wrong-but-in-range line passes. Raising that coverage is a wiki-wide
style change across 17 articles plus a decision about the em-dash excerpt form already in use at
`config-layer.md:271-272`. It is the real fix for the drift class this story was filed against, and
it is bigger than this story. File at sprint-71 refinement.
