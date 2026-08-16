---
id: STORY-228
title: Five documentation leftovers from sprint 73 — one quarantined article whose rehab grew, and four smaller inaccuracies
type: chore
points: null
status: draft
refined: null
sprint: null
---

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

### 5. `frontend/src/nav/Icon.tsx` — the `zap` glyph is now unused
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

*(To be written at refinement.)* Item 1 should be scoped honestly: rehabilitating `frontend-zone.md`
may be most of this story's cost and could reasonably be split back out.

## Not in scope

Mojibake repair (**STORY-192** — and note that story must be **re-measured** first, since archiving
`sample-mode.md` removed roughly 110–142 of its sequences).

## Open Questions

1. Item 5: remove the unused glyphs, or document the registry as a catalogue and stop counting them?
2. Item 1: rehabilitate `frontend-zone.md` inside this story, or split it out once its true size is
   measured?
