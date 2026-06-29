# Sprint 23 — Review

**Date:** 2026-06-29
**Goal:** Stand up Zone 7 (frontend) — the operator cockpit's foundation (shell, six-tab nav, typed API
client, design tokens, frontend DoD gate) against the PO-supplied `DESIGN-airtable.md`.

**Committed:** 1 story / 5 pts. **Accepted:** 1 story / 5 pts (100%).

## STORY-015a — Frontend shell — ACCEPTED (5 pts)

### What shipped
A working operator-cockpit shell under `frontend/`: Vite + React 18 + TypeScript (strict) SPA, hash-routed
six-tab nav (Dashboard · Availability · Approvals · Check History · Maintenance · Publications), a design
token layer mirroring `DESIGN-airtable.md` (the binding PO-supplied design) with four health-state semantic
tokens (up→success, down→signature-coral, degraded→signature-mustard, maintenance→info), a typed `/api`
client proving the Dashboard's `GET /api/v1/components` endpoint (loading/error/retry, MSW-mocked), and a
real four-command frontend DoD gate. Dev talks to the API via Vite's proxy (no backend change, CORS deferred
to STORY-017). The six tab bodies are placeholders (stories 015b–015g).

### Process note
The PO took implementation ownership mid-sprint (handed the brief to an external implementer) and supplied
`DESIGN-airtable.md` as the binding design. Two earlier Sonnet dispatches were stopped before any code was
written (tree clean each time); the design reference was then threaded into the shell story AC4, the plan
T2, and all six tab stories before the external implementer built it (commit `35acaba`).

### Acceptance criteria — all MET
- **AC1** SPA scaffold builds, isolated from the Python backend (no backend change). MET.
- **AC2** Six-tab nav + client-side (hash) routing, active tab indicated, placeholder panels; RTL test
  drives nav render + tab switching. MET.
- **AC3** Typed apiClient (`/api` seam) + one proving endpoint with loading/error states; MSW-backed tests
  cover a genuine success + 500-error + retry path. MET.
- **AC4** Token layer mirrors `DESIGN-airtable.md` verbatim (colors/type/rounded/spacing) + the four health
  tokens; no raw hex in components; status by icon+label (SVG), never color alone. MET.
- **AC5** Four npm gate scripts exit 0; CLAUDE.md gained a Frontend (Zone 7) section + gate + tooling
  inventory (command-sync). MET.
- **AC6** Accessibility/responsive baseline: semantic `<nav aria-label>` + `aria-current` + `<main>`,
  viewport meta, SVG icons, focus styling. MET.

### Evidence
- **Frontend DoD gate green** on the clean committed tree `ad7d8f2` (orchestrator re-ran): `npm run
  typecheck` 0 · `lint` 0 · `test` **4 passed** · `build` 0.
- **Backend gate** unaffected — `35acaba`+fixes touched only `CLAUDE.md` + `frontend/` (byte-identical to
  the verified `ed19084`); spot-confirmed lint-imports 5/0, ruff clean. Implementer also reported all six
  backend gates green (pytest 426).
- **Spec: PASS** (orchestrator-verified AC1–AC6 after the spec Opus reviewer hit the ACCOUNT session limit).
  **Quality: REQUEST-CHANGES → resolved.** Opus quality confirmed the token layer, health states, and MSW
  tests are genuinely sound; flagged dead Vite-scaffold assets (incl. design-forbidden `hero.png`), a
  `:hover` rule against the no-hover policy, and a raw coral literal. All fixed inline (PO-authorized,
  `ad7d8f2`); gate re-run green.
- **Wiki compile pass** (`f34b07b`): new `frontend-zone.md` article; `dev-setup-and-dod.md` updated with the
  frontend gate + re-stamped. Sweep: 0 stale / 0 broken links across 12 articles.

### Open follow-ups (not blocking acceptance)
1. Inter loaded via a runtime Google Fonts `@import` — self-host as a follow-up (system fallback degrades
   gracefully; not a license issue).
2. Dashboard fetch split across an effect + the refresh handler with an `eslint-disable
   react-hooks/set-state-in-effect` — clean up when a router/data-hook lands with the tabs.
3. `README.md` is still the default Vite template (mentions unused Oxlint) — cosmetic.

## Outcome
Branch `sprint-23` (8 commits from `sprint-23-start` @ `69a85bc`) accepted and merged to `main`. Velocity:
5 committed / 5 accepted. Zone 7 now has a working shell + the `DESIGN-airtable.md` design system; the six
tab stories (015b–015g) build on it next.
