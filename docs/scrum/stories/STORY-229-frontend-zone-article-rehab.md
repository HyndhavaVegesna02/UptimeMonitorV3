---
id: STORY-229
title: Rehabilitate frontend-zone.md — a quarantined map article carrying 67 code_refs, three of which no longer exist
type: chore
points: 5
status: ready
refined: 2026-08-16   # sprint-74 refinement; SPLIT OUT of STORY-228 on measurement
sprint: null
---

## Why this is its own story

Split from **STORY-228** at sprint-74 refinement. STORY-228 filed it as one of five "documentation
leftovers" and asked, in its own Open Questions, whether it should be split out "once its true size
is measured". Measured at refinement:

| | |
| --- | --- |
| Article length | **634 lines** |
| `code_refs` | **67** |
| `code_refs` that no longer exist on disk | **3** |
| Facts section | **14 top-level + 11 nested bullets = 25** |
| Distinct path-shaped citations in Facts | **58** — of which **22 resolve, 36 do not** |
| Of those 36 unresolvable: **merely mis-rooted** | **33** |
| Of those 36 unresolvable: **genuinely gone** | **3** |

> ⚠ **The "~40 Facts" row in the first draft of this table did not reproduce and has been replaced.**
> Pre-lock verification re-counted: 25 bullets carrying 58 distinct citations. (`.scrum/backlog.yaml`
> records 35 for the same thing; the live figure is 36.) The estimate below is re-checked against
> the real shape, not the guess.

That is not a tidy-up item. Re-verifying forty Facts against sixty-seven paths is the largest single
wiki job in the backlog, and burying it inside a 2-point chore would have hidden it — which is the
estimation failure sprint 73's own retro praised catching in the other direction (STORY-155b's
5 → 7 re-price).

## State today, stated precisely

`docs/scrum/wiki/frontend-zone.md` has been **`status: stale` since 2026-08-12** — *before* sprint
73 touched anything. The sweep therefore skips it, correctly: **quarantine is the wiki protocol's
designed safe state, and a stale article is not a lie.** No gate is breached today and nothing here
is urgent.

What sprint 73 changed is the *cost*: STORY-155a deleted three of its `code_refs` —
`frontend/src/nav/SampleModeBanner.tsx`, `frontend/src/mocks/handlers/sampleMode.ts`,
`frontend/src/features/dashboard/useSampleMode.ts` (all three confirmed missing at refinement) — and
it still documents `putJson` at `:121` and `:138`, a helper deleted with the feature.

**So this story is not "fix a broken article". It is "decide whether this article should exist, and
if so pay to make it true."**

## The decision this story must make first

The wiki protocol (v2.3.0) routes knowledge before writing it: a test/lint beats CLAUDE.md, which
beats a `tier: reference` reason article, which beats a `tier: map` article — because only the map
tier has recurring cost. **A 634-line map article with 67 `code_refs` is the most expensive shape in
that scheme**, and it has been quarantined for over four months of sprints without anyone needing it.

That is evidence, and the story should weigh it honestly rather than assume rehabilitation is the
answer.

## Acceptance Criteria

- [x] **AC1 (the routing decision is made explicitly and recorded)** — decide, and write down why,
      which of these the article becomes:
      **(a)** rehabilitated as `tier: map` — all ~40 Facts re-verified, the 3 dead `code_refs`
      removed, `putJson` claims deleted, `status: verified`;
      **(b)** demoted to `tier: reference` — the *reasons* kept (why the frontend zone is shaped as
      it is), all `code_refs` and Facts dropped, never swept again;
      **(c)** archived, with `frontend/README.md` and `docs/scrum/wiki/frontend-zone.md`'s durable
      content folded into the places that are actually read.
      ⚠ **The decision is the deliverable.** Silently doing (a) because it is the default is what
      this AC exists to prevent — (a) is the only option with recurring cost.
- [ ] **AC2 (whatever it becomes, it is TRUE at the final HEAD)** — no Fact cites a path that does
      not exist; no Fact describes `putJson`, `SampleModeBanner`, `useSampleMode` or the sample-mode
      MSW handler as present.
      ⚠ **The draft said "verified by the Facts lint and the citation gate, not by reading". That
      was FALSE and is corrected here — pre-lock verification proved all three mechanisms are green
      RIGHT NOW, on the article this story exists because it is wrong:**
      `yt_wiki.py:262-263`'s `check_facts` **skips** any citation whose path does not resolve
      (`if not (root / cite_path).exists(): continue`), so a Fact citing a deleted file is silently
      exempt — exactly this story's case; the citation gate scores this article `baseline: 0`,
      *"vacuously clean -- no citations extracted"* (`test_citation_gate.py:216-220`), because
      `CITATION_RE` requires a `:NNN` and none of its 58 citations carry one; and **nothing in the
      repo checks that a `code_ref` exists on disk** — verified by grep across `yt_wiki.py`,
      `yt_gate.py`, `yt_selftest.py`, `tools/citation_gate.py`, `tools/citation_sweep.py`.
      **So AC2's evidence is a re-derived list of `code_refs` that do not resolve, which must be
      empty, stated in the story.** Reading is the only mechanism that can see this; say so.
- [ ] **AC3 (if (a): every re-verified Fact was actually checked — and MIS-ROOTED IS NOT GONE)** — a
      re-verification that restates a claim without opening the file is the exact failure sprint 73
      caught twice (`canonical-types-and-ports.md`'s "ten ports", `statuspage-publish.md`'s
      "unrelated story"). For each Fact, the cited path resolves and says what the Fact says.
      ⚠ **A path that is merely MIS-ROOTED is RE-ROOTED, not deleted.** Measured at pre-lock
      verification: of 36 unresolvable citations, **33 are re-rootable** (`api/client.ts` →
      `frontend/src/api/client.ts`, and 32 more written relative to `frontend/src/` — the same root
      cause STORY-223 documents) and **only 3 are genuinely gone** (`useSampleMode.ts`,
      `SampleModeBanner.tsx` ×2 spellings). **The draft's bare "deleted, not carried" would have
      destroyed 33 true Facts under an AC written to protect knowledge** — deletion is reserved for a
      claim whose subject no longer exists.
- [ ] **AC4 (if (b) or (c): the tier change is mechanically legal, and inbound refs are found by
      GREP, not by the link lint)** — `tier: reference` articles carry **no `code_refs` and no
      Facts** (`yt_wiki.py:376-387`); anything under `archive/` carries `archived_sprint` and
      `archived_reason` (`yt_wiki.py:388-399`). Match the full frontmatter shape of the closest
      precedent, `archive/sample-mode.md`: `tier: reference` + `status: archived` + both archived
      keys. *(`status: archived` is NOT enforced for files already under `archive/`, so copy the
      precedent rather than trusting the lint.)*
      ⚠ **"Verified by the link lint" was FALSE and is corrected:** `yt_wiki.py:403-412` resolves
      `[[slug]]` against `wiki/<slug>.md` **or `wiki/archive/<slug>.md`**, so every `[[frontend-zone]]`
      still resolves after archiving and the lint is CLEAN either way — it structurally cannot flag
      this. The references that actually break are plain paths it never scans: **`CLAUDE.md:86`**,
      **`docs/project-history.md:86`**, **`.claude/skills/council/council.config.yaml:10`** and
      **`.agents/skills/council/council.config.yaml:10`**. Find them by grepping `frontend-zone`
      across `CLAUDE.md`, `docs/`, `.claude/`, `.agents/`.
- [ ] **AC5 (`test_citation_gate.py` is re-derived LIVE — under EVERY branch, not just archiving)** —
      ⚠ **The draft claimed "option (c) moves the count again; options (a) and (b) do not." Pre-lock
      verification DISPROVED that BY EXECUTION and it is deleted.** Running the real tests with the
      tier patched to `reference` (option (b), nothing else changed) failed **two** assertions:
      `map_tier_count` 12 → 11 (`test_citation_gate.py:501`) and the BASELINE tier cross-check
      (`:325`, `:330-332`). Option (a) moves them too: this article contributes **0** citations today
      because none carry a line number, so an implementer following AC3 and writing `file:line` adds
      up to 58, taking `total` 191 → ~249 and `globally_distinct` 179 → ~237 (`:475`, `:484`).
      **Re-derive live at the final commit, whichever branch you chose**, and update in the same
      commit: `test_citation_gate.py:264`, `:268`, `:325`, `:330-332`, `:475`, `:480`, `:484`,
      `:501`, the prose at `:79-83`, `:126-134`, `:256-262`, and this article's BASELINE entry at
      `:216-220`. **Carry no figure from this story, the plan, or the board.**
- [ ] **AC6 (gate)** — the full nine-command gate exits 0 at the final HEAD, with counts recorded.
      Run the wiki sweep after the last commit and take what it returns.

## Estimate: 5

Option (a) is the expensive branch — ~40 Facts × opening the cited file — and it is the one that
cannot be shortcut, because AC3 forbids the shortcut. Options (b) and (c) are cheaper but require
the link and tier work in AC4.

⚠ **If AC1 chooses (a) and the Fact-by-Fact pass turns out to exceed the estimate, STOP and split
rather than skimping on AC3.** A half-verified map article restored to `status: verified` is
strictly worse than the quarantined article we have now — it would move a known-stale article into
the trusted-and-wrong state the whole protocol exists to make impossible.

## Not in scope

Mojibake repair (**STORY-192**). Any change to **`frontend/src/`** or to the frontend build config
(`frontend/*.json`, `*.ts`, `*.js`) — this is a documentation story and must not touch the SPA.

> ⚠ **Corrected at pre-lock verification.** The draft forbade "any change to `frontend/` source",
> which **contradicted AC1 option (c)**, since that option requires folding durable content into
> `frontend/README.md` — a file under `frontend/`. That is the "three rules and no legal move" shape
> caught in sprint 73's plan verification. **`frontend/README.md` is explicitly permitted.**

## Open Questions

None blocking. AC1's choice is the implementer's to make and justify, and the PO can overrule it at
review; it is deliberately not pre-decided here, because the evidence for it lives in the article.
