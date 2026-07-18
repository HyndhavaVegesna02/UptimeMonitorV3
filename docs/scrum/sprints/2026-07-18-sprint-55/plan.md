# Sprint 55 — UI rewrite wave 1: foundation + shell

**Goal:** The new identity exists and the app lives inside it: Mission Teal design system
(dark-first bento, new type stack) + the new sidebar-less shell, all six routes rendering.

**Mode:** in-process. **Branch:** `sprint-55` (off `ui-rewrite`, which is off MAIN at
517fc38 — NOT off ui-redesign; that initiative is parked per the PO's 2026-07-18 pivot).
Merges to `ui-rewrite` at review; main untouched until the PO's final review.
**PO delegation:** unchanged (plans + per-sprint verdicts delegated; final merge is PO's).

**Plan-verifier: SKIPPED** (token economy rule) — frontend-only rewrite against existing
consumed DTOs; no new contracts; in-process.

**Design authority:** `docs/scrum/ui-rewrite/design-brief.md` (binding) over
`design-system/uptime-monitor-v3-rewrite/MASTER.md` (generated base). Salvage list in the
brief §Salvage — port logic (formatters, hooks, a11y contracts) from `ui-redesign`, never
the look.

**Tooling change declared at planning (freeze-compliant):** add @fontsource/space-grotesk,
@fontsource/inter, @fontsource/jetbrains-mono (fonts only, no runtime JS deps).

**Baseline:** main @ 517fc38 = sprint-51's accepted state (8/8 gate at 3cdf09d + doc
commits). The `.claude`-ruff-exclude fix lives on ui-redesign only — re-apply it here
FIRST (cherry-pick 203ed93) or the full gate false-reds on the installed skills.

**Verification:** live Playwright per story (retro-52 A1/A2 protocols in force — isolated
gate DB, HMR/:focus-visible false-alarm rules). Dev stack must be restarted on this branch.

## Execution order & steps

### 1. STORY-103 — Design foundation (3 pts)
- [x] Step 0: cherry-pick 203ed93 (.claude ruff exclude) + npm install the three @fontsource packages
- [x] Step 1: tokens.css v2 (both themes, dark default) + global.css + type stack — token tests where testable
- [x] Step 2: theme engine port (resolveTheme/ThemeContext/pre-paint) on data-theme, dark default
- [x] Step 3: primitives: Tile, Button, StatusBadge, Icon, RelativeTime (+ ported lib/: formatTime, formatLocation, useMediaQuery, breakpoints, matchMedia stub) — tests first
- [x] Step 4: minimal boot shell placeholder on new tokens (old skin dead)
- [x] Step 5: suite green; scoped DoD gate
- [x] Step 6: live gate: fonts self-hosted (network audit), theme toggle + no-flash, contrast spot checks both themes
- [x] Reviews: spec ∥ quality (3-pointer)

### 2. STORY-104 — App shell (3 pts)
- [ ] Step 1: top command bar + horizontal tab nav (aria-current, keyboard) — tests first
- [ ] Step 2: overall-status dot (worst-of) + "Updated Xs ago"
- [ ] Step 3: sample-mode switch/chip/banner (ported contracts) + theme toggle
- [ ] Step 4: ≤768px sheet nav (ported focus contract); 390px fit
- [ ] Step 5: suite green; scoped DoD gate
- [ ] Step 6: live gate: six routes render, zero console errors, drawer contract, 390 sweep
- [ ] Reviews: spec ∥ quality (3-pointer)

**Sprint close:** full 8-command gate (isolated DB) → wiki blast radius (frontend-zone.md
will need a REWRITE-era rework — expected big diff) → journal → delegated review → merge
`sprint-55` → `ui-rewrite` → retro → sprint 56 planning (STORY-105 dashboard + 106
availability).
