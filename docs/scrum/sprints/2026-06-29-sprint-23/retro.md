# Sprint 23 — Retro

**Date:** 2026-06-29
**Sprint:** STORY-015a (5 pts committed / 5 accepted). The first frontend sprint — Zone 7 shell.

## What went well
- **Clean accept after one inline fix-round.** The external implementer produced a sound shell: the
  `DESIGN-airtable.md` token layer mirrored verbatim, the four health tokens correct, status by icon+label
  (SVG, not color-alone), and MSW tests that genuinely drive a success+error+retry path (the Opus quality
  reviewer verified the tests aren't rigged). All four frontend gates + the backend gate green.
- **The design-reference pivot was absorbed cleanly.** When the PO supplied `DESIGN-airtable.md` as the
  binding design, it was threaded into the shell story AC4, the plan T2, and all six tab stories, and saved
  as a project memory — so every future tab story (and session) inherits it.
- **The new zone got proper knowledge hygiene:** a new `frontend-zone.md` wiki article + the frontend gate
  documented in CLAUDE.md and `dev-setup-and-dod.md`. Sweep: 0 stale / 0 broken links.

## What caused friction (workflow, not code)
- **The design source arrived after planning + dispatch.** Planning had locked "generate a design system
  via ui-ux-pro-max"; the PO then supplied `DESIGN-airtable.md`, stopping two Sonnet dispatches (no code
  written, tree clean) and forcing a re-thread of the shell + 6 tab stories. The handoff to an external
  implementer also came mid-sprint. No scope change, but avoidable churn.
- **`npm create vite` boilerplate reached review.** The generator left `hero.png` (chrome the binding
  design explicitly forbids), `react.svg`/`vite.svg`, `public/icons.svg`, a purple template favicon, a
  `<title>frontend</title>`, and the default README in the commit — the quality reviewer's blocking finding.
- **Single-commit cadence (external).** The whole story landed in one commit despite the brief's
  commit-after-green cadence. Inherent to external implementation (the orchestrator can't enforce a
  subagent-style cadence on an outside agent) — noted, not amended.

## Amendments
- **ADOPTED (PO-approved 2026-06-29):** *A story that runs a project generator prunes the generator's
  boilerplate before the gate — committed scaffold residue is a review-blocking finding.* Written into
  `.scrum/working-agreements.md` with the motivating incident.
- **PROPOSED, NOT adopted:** "Confirm a binding reference design at planning before locking the design
  approach." The PO declined to make it binding this time. Recorded here as a retro observation; the
  `frontend-design-reference` memory now carries the design source so future UI stories inherit it.

## Carry-forward (backlog candidates, not amendments)
- Self-host Inter instead of the runtime Google Fonts `@import` (perf/CSP/offline).
- Clean up the Dashboard fetch (effect + handler split with an `eslint-disable`) when a router/data-hook
  lands with the tabs.
- Trim the default Vite README (mentions unused Oxlint).
- These fold naturally into the first per-tab story (STORY-015b, Dashboard) or a tiny frontend-polish chore.

## Process metrics
- Reviewer rejections: 1 quality REQUEST-CHANGES (resolved inline), 0 spec (spec Opus reviewer hit the
  account session limit → orchestrator-verified AC). Fix loops: 1. Hotfixes: 0. Blocked: 0.
- Dispatches stopped by PO before any code: 2 (workflow redirection, not failures).
- Estimate accuracy: 5 pts, single story, no overrun. Velocity: 5/5. Last-4 (20,21,22,23) = 5,5,3,5.
