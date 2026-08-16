---
id: STORY-228
title: Four documentation leftovers from sprint 73 — each in a place the wiki protocol deliberately does not look
type: chore
points: 2
status: draft   # NOT READY -- AC4's Open Question is UNANSWERED, so it fails the Definition of
                # Ready and CANNOT enter a sprint. Held out of sprint 74 for that reason, not on
                # capacity. Ask the PO the Icon-registry question, then this is a 2 and refinable.
refined: 2026-08-16   # sprint-74 refinement. SPLIT: item 1 became STORY-229 on measurement.
sprint: null
---

> **SPLIT AT REFINEMENT (2026-08-16).** As filed this story carried five items, and its own Open
> Question asked whether item 1 (`frontend-zone.md`) should be split out "once its true size is
> measured". It was measured: **634 lines, 67 `code_refs`, ~40 Facts, 3 refs already missing from
> disk.** That is not a tidy-up item — rehabilitating it is a story. It is now **STORY-229**, and
> this story keeps the four genuinely small items below.

## Where this came from

Filed at the **sprint-73 review** on PO instruction ("file for fixing the minors"). Five
quality-review findings, none of which breached a gate — the wiki sweep, link lint and integrity
check were all CLEAN at sprint close, and these survived precisely *because* the mechanisms
correctly quarantined or ignored them.

That is the theme worth stating: **every item here is somewhere the automated wiki protocol
deliberately does not look.** None of them can be caught by tightening the sweep.

## The five

### 1. `docs/scrum/wiki/frontend-zone.md` — a quarantined article whose rehab cost grew
Already `status: stale` since 2026-08-12, so the sweep skips it (correctly — quarantine is the
protocol's designed safe state). STORY-155a then deleted three of its `code_refs`
(`SampleModeBanner.tsx`, `useSampleMode.ts`, `mocks/handlers/sampleMode.ts`) and it still documents
`putJson` at `:121`/`:138`, a helper that no longer exists.

**No gate breach, and it is not "wrong" in the trusted sense — it is visibly stale, which is the
protocol working.** But its eventual rehab pass is now larger than when it was quarantined, and
nothing will surface that fact until someone opens it. **Largest of the five.**

### 2. `tools/demo_engine/README.md:161` — a dated claim that is now false
Still says "AC1(a)-(e) all recorded". STORY-155b retired AC1(c) (the `GET /sample-mode` check) from
`tools/demo_loop_gate/harness.py`. It is a dated historical record of a past run, and it sits under
`tools/`, which **no DoD command lints and no wiki mechanism sweeps** — the same blind spot that
made STORY-155b's AC10 necessary.

### 3. `docs/scrum/wiki/zone-rules.md:57-100` — four separate STORY-155b blocks for one story
Self-inflicted ordering: STORY-155b landed its `harness.py` edit *after* its wiki pass, which
shifted line-numbered citations and forced re-keying, then a test rename forced a fourth touch. The
reviewer verified every re-derived line number is **exact at HEAD** — the final state is coherent,
not merely green. This is a readability item: one consolidated entry says the same thing.

### 4. `docs/scrum/wiki/config-layer.md` — a citation outside the article's own `code_refs`
It cites `backend/src/adapters/outbound/statuspage/__init__.py:54`, which is not among its three
`code_refs`. So if that file drifts, **this article will never be re-triggered by the sweep** — the
staleness mechanism is keyed on `code_refs`, and a citation outside them is invisible to it. It
matches the article's pre-existing "Seven surviving readers" pattern, so this is a known shape, not
a novelty.

### 5. `frontend/src/components/Icon/Icon.tsx` — the `zap` glyph is now unused
STORY-155a deleted its only consumer. The reviewer judged it **not that story's debt**, because the
registry already carries unused `search`, `trash` and `x` — it is a catalogue ported verbatim from
the design mock, not a use-list. Included here for completeness; the honest options are "remove all
four" or "document that the registry is a catalogue and stop treating unused entries as debt."

## Explicitly NOT filed here — it belongs to STORY-223

The sixth carried item, **pre-existing unresolvable citation debt in `zone-rules.md` (6) and
`demo-engine.md` (8)**, is already the subject of **STORY-223** ("Wiki Fact citations that do not
resolve from the repo root — 146 across 11 articles"). Verified at filing rather than assumed. It is
recorded as a note on STORY-223, not duplicated into a new story.

## Acceptance Criteria

- [ ] **AC1 (the false claim in `tools/` is corrected)** — `tools/demo_engine/README.md:161` no
      longer asserts "AC1(a)-(e) all recorded". It states which sub-AC was retired, by which story,
      and why. ⚠ **Nothing lints this file** — no DoD command touches `tools/`, and the wiki
      mechanisms do not sweep it — so the correction must be verified by reading, and the AC is met
      by showing the new text, not by a green command.
- [ ] **AC2 (`zone-rules.md`'s four STORY-155b blocks become one)** — the four separate entries at
      `:57-100` are consolidated into a single History entry that says the same thing. **No claim
      may be dropped in the merge**: the consolidated entry still names the `harness.py` line shifts,
      the ZR-3 re-key, and the citation-count re-derivation. State the before/after line count.
- [ ] **AC3 (`config-layer.md`'s out-of-`code_refs` citation is resolved)** — it cites
      `backend/src/adapters/outbound/statuspage/__init__.py:54`, which is not among its `code_refs`,
      so drift in that file can never re-trigger this article. ⚠ **It is cited TWICE — `:103` and
      `:451`** (found at pre-lock verification); handle both. Resolve it **either** by adding the
      path to `code_refs` **or** by removing the citation — and state which, and why. ⚠ Adding it
      widens the article's sweep surface; that is a real cost, not a free fix.
- [ ] **AC4 (the `Icon` registry question is answered in writing, not left implicit)** — per the
      PO's ruling on the Open Question below, either the unused glyphs (`zap`, `search`, `trash`,
      `x`) are removed, or a comment in `frontend/src/components/Icon/Icon.tsx` records that the
      registry is a **catalogue ported from the design mock** and that unused entries are expected.
      Silence is not an outcome: today a reader cannot tell dead code from deliberate inventory.
      ⚠ **Path corrected at pre-lock verification** — the draft said `frontend/src/nav/Icon.tsx`,
      which does not exist (`frontend/src/nav/` holds only `Sidebar.*`, `TopBar.*`, `sidebarState.*`,
      `tabs.ts`). The registry is at `frontend/src/components/Icon/Icon.tsx` (`zap` at `:74`, the
      `IconName` union at `:23-28`).
      ⚠ **If the REMOVE branch is chosen, `frontend/src/components/Icon/Icon.test.tsx:21-40` must be
      updated in the SAME commit** — it enumerates all 18 names in an `as const` array including
      `search`, `x`, `trash`, `zap`. Removing them from the union without touching that array is a
      TypeScript error, so `npm run build` (`tsc -b`) fails: **gate-red on DoD command 7.**
      ⚠ **The remove branch also collides with STORY-229.** `Icon.tsx` is `code_ref` #23 of
      `frontend-zone.md`. If 229 lands option (a) and sets `status: verified`, this edit re-stales
      that article at final HEAD (`yt_wiki.py:201-225` diffs refs from the article's own last
      commit) — silently undoing 229's centrepiece. If both stories are ever in one sprint, either
      run this one FIRST or commit a same-commit re-verification touch of `frontend-zone.md`.
- [ ] **AC5 (the citation-gate numbers are re-derived — AC2 and AC3 MOVE them) — added at pre-lock
      verification, and a gate-red if missed.** ⚠ **The draft had no AC for this at all.**
      `zone-rules.md:57-100` is inside the **frontmatter comment block** (it closes at `:101`), and
      `tools/citation_gate.py:75,82` scans the whole file, frontmatter included. Two citations live
      in the region AC2 consolidates: `run.py:182-184` at `:65` and `harness.py:62-69` at `:74`.
      **`harness.py:62-69` occurs NOWHERE ELSE in that article**, so if the merged prose does not
      re-quote it, `total` goes 191 → 190 and `globally_distinct` 179 → 178, reddening
      `test_citation_gate.py:475` and `:484`. Simulated at verification; whether it fires depends on
      wording an implementer cannot know to weight.
      AC3 has the same shape: `config-layer.md` carries that statuspage citation **twice**
      (`:103` **and `:451`**) — removing only one is a no-op for the gate, removing both moves the
      totals.
      **Re-derive `test_citation_gate.py:475`, `:484` (and `:501` if any tier moves) live at the
      final commit, and update the module docstring in the same commit.**
- [ ] **AC6 (gate)** — the DoD commands the diff can affect exit 0 at the final HEAD. Run the wiki
      sweep after the last commit and take what it returns; do not pre-declare a blast radius.

## Estimate: 2

Four small, independent edits. The only judgement calls are AC3's either/or and AC4's, and both are
one-line decisions once made. Nothing here needs a test, which is precisely why none of it was
caught automatically.

## Not in scope

`frontend-zone.md` — **now STORY-229**. Mojibake repair (**STORY-192** — and that story must be
**re-measured** first, since archiving `sample-mode.md` removed roughly 110–142 of its sequences).

## Open Questions

1. **AC4 — the PO decides:** remove the four unused glyphs, or document the registry as a catalogue
   and stop treating unused entries as debt? *(Asked at sprint-74 refinement. The reviewer's own
   view was that this is not debt — the registry was ported verbatim from the design mock — which
   argues for documenting rather than deleting.)*
