# Sprint 38 Review — Operator Dashboard redesign

**Branch:** `sprint-38` (cut from `main` @ `c548c39`, tag `sprint-38-start`) · **Committed:** 31/31 points across 8 stories · **Status:** awaiting PO verdicts. Nothing merged to `main`.

**Goal met:** the six-tab operator SPA is re-skinned to the imported *Operator Dashboard* design —
collapsible icon sidebar, Geist type, 7-status palette, cards/grids/timeline — with every element
bound to REAL API data (no fakes), all functionality/routing/business-logic preserved, and an
EMPTY backend diff throughout. Backend data gaps are filed as follow-ups (063–067), not faked.

## Gate (authoritative, on the fully-integrated branch @ `f1c3d9e`)
- `npm test` → **50 files / 355 passed** (exit 0) · `npm run build` → exit 0 · `npm run lint` → exit 0
- `git diff sprint-38-start..HEAD -- backend/ scripts/ config/ migrations/ pyproject.toml alembic.ini` → **empty**
- Backend six-gate carried by the empty backend diff (last green: sprint-37, 513 passed).

## Stories (all Done — spec PASS / quality APPROVE unless noted)

| Story | Pts | Result |
|---|---|---|
| **055** Design-system foundation + primitives | 5 | Retuned tokens (both themes), self-hosted Geist/Geist Mono, 7-status palette (+partial/+missing), shadow token, Icon set, restyled base components, shared `Table`/`UptimeBar`/`SummaryCard`/`Timeline`. spec PASS / quality APPROVE. |
| **056** App shell | 5 | Collapsible left icon sidebar + top bar (theme toggle + **relocated sample-mode ⚡ trigger**) + banner + Approvals count badge; replaced top `Nav`. spec PASS / quality APPROVE. Recovered from a session-limit crash (attempt 1 committed nothing). |
| **057** Dashboard | 5 | Summary cards + grouped expandable rows + signal drill-down + `UptimeBar` (real data, graceful no-data) + preserved maintenance badge. spec PASS / quality APPROVE. Its hook layer survived a session-limit crash and was recovered by merge. **PO note:** h1 reads "Dashboard" (not the mock's "System health") to keep the shell test invariant (h1 == nav label). |
| **058** Availability | 3 | Grid + segment bars + hatched completeness + legend + window toggle + drill-down. 0-1 fraction scale verified end-to-end. spec PASS / quality APPROVE. |
| **059** Approvals | 5 | Card layout + severity stripe (derived from `to_status`) + from→to pills + confirm flow + "Queue clear". spec PASS / quality APPROVE. |
| **060** Check History | 3 | Filter toolbar (search + result + location + window) + dense grid; **resolved the STORY-054 flake** (1000-row cap preserved via injectable prop; cap test no longer renders 1000 rows). spec PASS / quality APPROVE-after-fix (2 MAJORs — reduced-motion guard + cap-restore — fixed in one loop). |
| **061** Maintenance | 3 | Two-column form-card + windows list with state badges; inline 422 mapping preserved. spec PASS / quality APPROVE. **PO note:** h1 "Maintenance" (mock: "Scheduled maintenance"); subtitle matches mock. |
| **062** Publications | 2 | Vertical `Timeline`. Gate-only (2 pts), green. |

## Adapt-to-real-data omissions (per PO decision; filed as backend follow-ups)
- **063** proposal severity/reason/source/triggering-signals · **064** observation HTTP code + check type ·
  **065** maintenance title + DELETE · **066** publication author/outcome/incident ·
  **067** component grouping + per-component uptime-bucket API.
Each design element that would need data the API doesn't expose was OMITTED (never faked), and the
gap captured above.

## Execution notes (for the retro)
- **Parallel multi-agent execution** (PO-directed): wave 0 (055 solo) → wave 1 (056 solo) → wave 2
  (057–062, two parallel worktree batches). 059+062 and 058+060+061 ran concurrently in isolated
  worktrees, integrated serially with per-story Opus reviews + serial gates.
- **Session limit** (account-level) crashed 056-attempt-1 and 057-attempt-1 mid-run; both recovered
  cleanly via per-step commits (056 committed nothing → fresh redo; 057's committed hooks → merged +
  finished). No work lost.
- **PO decisions requested at review:** (1) the two h1 strings ("Dashboard"/"Maintenance" vs the
  mock's "System health"/"Scheduled maintenance") — keep, or update the shell-test invariant to use
  the mock copy? (2) Check History cap stays at the preserved 1000.

## Follow-ups filed
- **068** (defect) `useAvailability.test.tsx` parallelism false-red — make the gate deterministic.
- **069** (chore) redesign consolidation minors (uptimeSegments dedup, stale docstrings, token/a11y nits).

## Not done at review (honest)
- **Live render-vs-wire spot check deferred** — the backend was not running (`:8000` down) at close.
  Low risk here: empty backend diff (no DTO change), the historical scale-drift risk was
  reviewer-verified, and all pages are MSW-tested against real-shape fixtures. Recommend the PO run
  `npm run dev` + the local stack (CLAUDE.md recipe) to click through, or ask the orchestrator to
  bring the stack up and drive a browser pass.
