# Sprint 25 — Review

**Date:** 2026-07-02
**Goal:** rebuild the frontend zone — the shell (STORY-015a) — guided by `DESIGN-linear.app.md`
(guide, not copy), with dark + light themes, so tabs 015b–015g become pure fill-ins.
**Committed / delivered:** STORY-015a (5 pts). Single-story focused sprint (velocity mean 4.33).
**Branch:** `sprint-25` (tag `sprint-25-start` @ `521764c`). Story commits `f7bbcdc..08d91e7` (7).
**Mode:** in-process implementation — Sonnet 5 implementer at high effort (PO directive 2026-07-02),
Opus spec + quality reviewers.

## STORY-015a — Frontend shell (5 pts) — ACCEPTED PENDING PO VERDICT

The frontend zone, second attempt (the first, sprints 23–24 on `DESIGN-airtable.md`, was reverted
in `521764c`). A Vite + React + TS-strict SPA under `frontend/`, isolated from the backend, with:
a theme-scoped token layer (dark = Linear-reference-native, light = derived) with a flash-free
persisted toggle; shell primitives (Button / StatusBadge / Panel / Loading·Error·Empty states); a
six-tab nav + client-side routing; a typed `/api` client with `GET /api/v1/components` proven end
to end (loading / error+retry / empty / success) over an MSW test harness; and the three frontend
DoD gates activated.

### AC checklist (spec reviewer — all MET)
- **AC1** SPA builds (`tsc -b && vite build` exit 0) + dev `/api` proxy; boilerplate pruned; no
  backend source change (only pyproject's ruff `frontend` exclude). MET.
- **AC2** Six routed tabs from single-source `nav/tabs.ts`; active = ink + accent border; test
  drives a click that switches the panel. MET.
- **AC3** Typed `apiClient` (single `/api` seam) + DTOs mirroring the backend; components endpoint
  wired with all four states; MSW test drives success + error→retry (asserts callCount==2). MET.
- **AC4** `styles/tokens.css` theme-scoped; dark values verbatim from the reference, light derived;
  no raw hex in components (grep-clean); Inter + JetBrains Mono via @fontsource (no runtime CDN);
  health tokens in both themes with `-subtle` variants; all primitives present. MET.
- **AC5** Default = `prefers-color-scheme`; toggle overrides + persists; pre-paint inline script
  (no flash); tests cover system-default / override / persistence. MET.
- **AC6** Accent focus ring on all interactive elements; status = dot + label (never color-alone);
  every ink-as-text token ≥4.5:1 in BOTH themes (reviewer-computed; worst 5.14:1); ≥40px targets. MET.
- **AC7** `npm test` / `npm run build` / `npm run lint` all exit 0, activated in
  `.scrum/definition-of-done.md` + documented in CLAUDE.md in the same commit (08d91e7). MET.

### DoD evidence — all nine gates green at `08d91e7` (clean committed tree)
- Backend: pytest 426 passed (throwaway postgres:16); lint-imports 5/0; check_fk_direction 11/0;
  `python -m alembic upgrade head` exit 0; ruff check clean; ruff format 153 files clean.
- Frontend (from `frontend/`): npm test 63 passed / 0 skipped; npm run build exit 0; npm run lint exit 0.

### Reviews
- **Spec (Opus): PASS** — all 7 AC MET; ran the frontend gates itself, computed contrast, traced
  each "tested" AC to a test that drives the named path.
- **Quality (Opus): APPROVE** — 0 Critical, 0 Major. Race-safe fetch hook, flash-free theme system,
  airtight token layer, tests assert real behavior via MSW only (clean against the project's three
  prior "green-test-wrong-path" incidents). Six non-blocking minors → **STORY-041** (backlog chore).

### Follow-up captured
- **STORY-041** (chore, 2 pts, ready): client error-wrapping on malformed 2xx body, shared `cx()`
  helper, modular MSW handlers, catch-all route — harden the template before the tabs copy it.

## Wiki compile pass (blocking; complete)
NEW `frontend-zone.md`; `dev-setup-and-dod.md` updated (frontend 3-command gate live + ruff
`frontend` exclude + `code_refs`); `api-five-file-convention` / `architecture-boundary` /
`config-layer` re-verified (pyproject `frontend` ruff-exclude only, Facts unaffected). Mechanical
sweep: 0 stale / 0 broken links across all 12 articles.
