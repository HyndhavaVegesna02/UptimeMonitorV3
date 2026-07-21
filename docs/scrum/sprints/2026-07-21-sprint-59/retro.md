# Sprint 59 — Retro

Process inspection (not product). Sprint 59 rebuilt the frontend greenfield: design system (120),
collapsible shell (121), Dashboard on real data (122). All three accepted; velocity 9/9.

## What the process did well
- **The review layer earned its keep on every story.** All three stories had ≥1 review rejection
  that caught a REAL, fixed-before-ship defect — and quality review found something in all three.
  Not a red flag: the gates are working exactly as intended on a UI that had been rejected twice.
- **Crash recovery held.** STORY-121's first implementer hit a usage limit mid-story; the
  commit-after-every-green-step cadence + a board-recorded resume point meant zero lost work — 4
  green commits preserved, coherent uncommitted work kept, one orphan scrap discarded, resumed clean.
- **The reality gate was load-bearing, repeatedly.** It caught the exact defects the green test
  suite could not (see below) and verified truthful rendering number-by-number against the live API.

## What cost us / recurred
1. **A whole class of frontend defects passed green jsdom/MSW tests and were caught only by a
   reviewer reading CSS/labels or by the live reality gate** — three instances this sprint:
   (a) STORY-120 Sparkline animated `stroke-dashoffset`; its jsdom test asserted the CSS TEXT and
   *documented* the AC breach as expected; (b) STORY-121 the pre-paint collapse class outlived
   hydration (a CSS-specificity/hydration bug jsdom cannot execute — invisible to the entire suite,
   caught live); (c) STORY-122 the chart legend said "Median response" over a raw per-check series.
   Common mechanism: **asserting source text (CSS/DOM string) is not asserting rendered behavior.**
2. **MSW's instant mocks hid a real live-backend problem.** STORY-122's Dashboard rendered correct
   values in tests but, against the real backend, hung ~20–120s in "Loading…": the `/availability`
   24h computation is slow on DynamoDB-Local (single-threaded, serializes everything behind it), and
   the frontend couples the fast history fetch and the slow availability fetch in one `Promise.all`,
   so nothing paints until the slowest returns. Zero-latency mocks make this structurally invisible
   to unit tests — only the live reality gate exposed it. (Filed STORY-127/128.)
3. **Orchestration miss (self-inflicted, caught by review):** I instructed the implementer to defer
   the CLAUDE.md frontend-section update to sprint close; quality review correctly flagged that a
   stale CLAUDE.md would misdirect the *next* implementer at session start. The DoD "CLAUDE.md
   updated in the same commit on a stack/architecture change" rule already covers this — the rule
   worked; my orchestration deviated from it. No new rule needed; noted as an orchestration-discipline
   reminder.
4. **Minor friction (no amendment):** the baseline gate came up RED from a stale `uptime_dynamo`
   container breaking the session-scoped pytest fixture (51 errors) — correctly discounted per the
   2026-07-06 "prove contention before discounting" agreement and resolved by removing the container;
   root mechanism uncertain (the fixture uses unique names + ephemeral ports), so no reliable
   mechanical fix identified — a blind "reap stale containers" guard was considered and set aside as
   cargo-cult. `ui-ux-pro-max` lived at `.agents/skills` not `.claude/skills` (stale bytecode);
   subagent dispatches hit transient 529s during the wiki compile (done inline instead).

## Amendments (PO-approved 2026-07-21 — both landed)

### A1 — tests-that-lie taxonomy gains member #7: "source-text-as-proof" (Rung: checklist) — LANDED in `.scrum/checklists/quality-review.md`
Add to `.scrum/checklists/quality-review.md`'s tests-that-lie taxonomy:
> **7. Source-text-as-proof** — a jsdom/DOM test asserts the SOURCE text (a CSS rule string, a class
> name, an attribute) as a proxy for a real-browser behavior it cannot execute (cascade, specificity,
> hydration, paint, motion). A wrong CSS property, a class that outlives hydration, or a mislabeled
> series passes green. Necessary but NOT sufficient: any motion-property/cascade/hydration/visual-
> label claim must be confirmed by the live reality gate, not a CSS-text assertion alone. (sprint-59:
> Sparkline `stroke-dashoffset`, the pre-paint collapse-class hydration bug, the "Median" mislabel.)

### A2 — reality gate for a consumer story observes live FIRST-PAINT/latency, not just value-correctness (Rung: checklist) — LANDED in `.scrum/checklists/implementer.md`
Add to `.scrum/checklists/implementer.md` (reality-gate discipline) + honored by the orchestrator:
> A consumer/rendering story's live reality gate observes first-paint BEHAVIOR against the REAL
> backend, not only the correctness of rendered values: a region that hangs on a slow/serialized
> endpoint, or fast regions gated behind one slow fetch (coupled `Promise.all`), is a finding. MSW's
> zero-latency mocks hide this — it is only visible against the live stack. (sprint-59 STORY-122: the
> Dashboard rendered correct values but hung 20–120s on the slow `/availability` fetch it had bundled
> with the fast history fetch.)

Both are checklist-rung (the lowest rung that mechanically binds a reviewer/implementer here — the
behaviors resist a pure gate-command check). Prose was rejected as too weak; a gate command can't
judge "hangs too long" without a brittle threshold.
