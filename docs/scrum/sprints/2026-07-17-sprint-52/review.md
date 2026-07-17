# Sprint 52 Review — 2026-07-17

**Verdicts under PO delegation** (initiative directive 2026-07-17: per-sprint review
verdicts pre-approved; the final merge of `ui-redesign` into main remains the PO's).
Merge target: `ui-redesign` (integration branch) — main untouched.

## STORY-096 — Responsive shell (3 pts) — ACCEPT

Demo evidence (all live Playwright against the running local stack, screenshots in
`gate-096/`):
- 390×844: all six tabs fit exactly (documentElement.scrollWidth == 390, no page H-scroll);
  nav is a closed-by-default overlay drawer with labeled hamburger trigger, scrim, Escape /
  scrim-click / nav-link close, focus into the drawer on open and back to the trigger on
  close.
- 1024px: auto icon-rail (52px). 1440px: expanded sidebar (212px) exactly as before, user's
  stored expand/collapse preference honored.
- Sample-mode banner: 57px (~1–2 lines) at 390 (was a 5-line column).
- Reviews: spec APPROVE (5/5 AC → test trace; constraint fence clean: frontend-only, no new
  deps), quality APPROVE (0 critical/major; tests-that-lie verdict CLEAR).
- Suite: 363 → 400 tests.

**Reality-gate catch:** tapping a drawer nav link navigated but left the drawer covering the
destination page — invisible to jsdom tests, caught live, fixed (`ff0779e`) and re-verified
live. This is exactly what the reality gate exists for.

## STORY-097 — Consistent page scaffold (2 pts) — ACCEPT

Demo evidence (live Playwright, screenshots in `gate-097/`):
- Mechanical audit across all six tabs: exactly one h1 per page, rendered by the shared
  `PageHeader` outside any card, heading levels sequential.
- One width policy: `--container-width: 960px` token (`.page`) with explicit `.page--wide`
  opt-in for the three dense tabs; 960 matches Approvals' pre-existing shipped width.
- Designed `EmptyState` (icon + helpful copy) on Maintenance, Publications, Check History
  (filtered-to-zero, exercised live via a no-match search), Approvals (pre-existing, now via
  the shared primitive); Publications no longer claims "showing the latest 50" when empty.
- Availability's legend + range switcher moved into the PageHeader actions slot; switcher
  re-verified functional after the move.
- STORY-096 non-regression re-run: six tabs at 390 all fit; drawer opens/Escape-closes.
- Suite: 400 → 417 tests.

## Sprint outcome
- Velocity: **5/5** (both stories accepted).
- Final full 8-command gate: GREEN at `45c6086` (evidence in `sprint-current.yaml`),
  run with an isolated test DB; live local stack verified intact afterward.
- Merged: `sprint-52` → `ui-redesign` (main untouched, per initiative rules).

## Accepted-with-notes (folded into future initiative stories, no new story filed)
- Quality-review minors: breakpoint tokens in `tokens.css` are documentation-only mirrors
  (comment in place, acceptable); `Table.test.tsx` class-name assertion (jsdom limitation,
  acceptable); shift+Tab trap test — landed with `ff0779e`.
- Implementer candidates: Check History's *unfiltered* empty state could adopt the icon
  treatment (fold into STORY-101's table work); Approvals card list has no `Panel` wrapper
  (fold into STORY-100's card redesign); 5 pre-existing ad-hoc `mockMatchMedia` copies could
  move to the shared helper (opportunistic cleanup in any later frontend story).

## Blockers raised
None. No hotfixes, no interrupts, no PO-input-required questions.
