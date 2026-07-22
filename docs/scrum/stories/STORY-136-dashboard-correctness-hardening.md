# STORY-136 — Dashboard/shell correctness hardening

- **Status:** ready
- **Points:** 3
- **Sprint:** 61
- **Type:** defect
- **Scope:** frontend only

## Context
From the 2026-07-22 design-QA review, verified against code + the live app. Three
correctness defects on the Dashboard/shell: a duplicate React key on the Recent-checks
feed (the same collision class STORY-130 fixed on History), the `unknown` health token
shown during the components load, and `useFetch` having no timeout (a hung request spins
forever). Note: error-state + retry ARE already wired — only the timeout is missing.

## Acceptance criteria
- **AC1** — The Dashboard "Recent checks" feed no longer keys rows by the colliding
  `signalKey-observed_at-location` triple (`deriveRecentChecks.ts:46`). Rows key on a
  guaranteed-unique discriminator (final sorted position, matching the STORY-130 History
  fix). A regression test builds a batch with a **duplicate `(signal_key, observed_at,
  location)` triple** and asserts no React duplicate-key warning + correct row count/order.
- **AC2** — While the components fetch is in flight, the topbar overall-status shows a
  **neutral loading treatment** (skeleton or "Updating…"), never the `unknown` health
  token. `unknown` renders only on a succeeded fetch that is genuinely unknown. Test: the
  loading-phase render is not the `unknown` StatusBadge; success-with-data is the real status.
- **AC3** — `useFetch` gains a **request timeout**; a never-settling request transitions to
  the error phase (surfacing the existing `ErrorState` + retry), not an infinite spinner.
  Test with a never-resolving fetcher + fake timers asserts the error phase + working retry.
  Existing error/retry behavior preserved.
- **AC4** — No regression: all six routes render; `npm test`/`build`/`lint` green.

## Design / skills
Fresh work on the sprint-59 design system; honor `ui-ux-pro-max`, `web-design-guidelines`,
`vercel-react-best-practices`, `emil-design-eng`, `design-system`. The loading treatment
for AC2 must be a real design-system state, not an ad-hoc string.
