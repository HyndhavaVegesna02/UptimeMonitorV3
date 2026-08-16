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
| Facts to re-verify | **~40** |

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

- [ ] **AC1 (the routing decision is made explicitly and recorded)** — decide, and write down why,
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
      MSW handler as present. Verified by the Facts lint and the citation gate, not by reading.
- [ ] **AC3 (if (a): every re-verified Fact was actually checked)** — a re-verification that
      restates a claim without opening the file is the exact failure sprint 73 caught twice
      (`canonical-types-and-ports.md`'s "ten ports", `statuspage-publish.md`'s "unrelated story").
      For each Fact, the `file:line` it cites resolves and says what the Fact says. Where a Fact
      cannot be checked, it is **deleted, not carried** — knowledge can be absent, never
      trusted-and-wrong.
- [ ] **AC4 (if (b) or (c): the tier change is mechanically legal)** — `tier: reference` articles
      carry **no `code_refs` and no Facts** (enforced), and anything under `archive/` carries
      `archived_sprint` and `archived_reason` (enforced at `yt_wiki.py:388-397`). Every inbound link
      is repointed or pruned, verified by the link lint.
- [ ] **AC5 (`test_citation_gate.py`'s baseline moves with it)** — the file's `BASELINE` dict and its
      article-count assertions must match. ⚠ **Re-derive the numbers live.** Sprint 73 moved them
      twice (17 → 16 articles; per-article and globally-distinct counts both shifted), and that
      file's own history records the count rotting every time someone restated it without measuring.
      Option (c) moves the count again; options (a) and (b) do not.
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

Mojibake repair (**STORY-192**). Any change to `frontend/` source — this is a documentation story
and must not touch the SPA.

## Open Questions

None blocking. AC1's choice is the implementer's to make and justify, and the PO can overrule it at
review; it is deliberately not pre-decided here, because the evidence for it lives in the article.
