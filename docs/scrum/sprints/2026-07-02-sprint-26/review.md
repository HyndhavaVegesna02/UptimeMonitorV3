# Sprint 26 — Review

**Date:** 2026-07-02
**Goal:** land the first real frontend tab (Dashboard) on a hardened shell.
**Committed / delivered:** STORY-041 (2) + STORY-015b (3) = 5 pts. Both Done.
**Branch:** `sprint-26` (tag `sprint-26-start` @ `9e9b369`). Commits `6e65f68..6d44c22`.
**Mode:** in-process — Sonnet 5 implementer at high effort; Opus spec + quality reviewers.

## STORY-041 — Frontend pattern hardening (2 pts) — ACCEPTED PENDING PO VERDICT
The six STORY-015a quality-review minors, tightened before the shell seams are copied across five
more tabs:
- **Client error-wrapping** (`api/client.ts`): a malformed-body `SyntaxError` on a 2xx is now
  wrapped into the typed `ApiError` — the client's contract holds on every path.
- **Shared `cx()` helper** (`lib/cx.ts`): the `[...].filter(Boolean).join(' ')` idiom, deduped out
  of `Button`/`Panel`.
- **Modular MSW handlers** (`mocks/handlers/<feature>.ts` composed in `handlers/index.ts`): a tab
  story now adds its own handler module, touching no other feature's.
- **Catch-all route** (`AppShell.tsx` → `pages/NotFoundPage.tsx`): unknown paths render a
  not-found panel instead of an empty `<main>`.

DoD (2 pts → gate only, no reviewers): all 9 gates green at `4489f9d` (frontend 68 tests / build /
lint; backend lint-imports 5/0, ruff clean, pytest 426; DB pair unaffected — frontend-only diff).

## STORY-015b — Dashboard tab (3 pts) — ACCEPTED PENDING PO VERDICT
The first REAL tab. The shell's `GET /api/v1/components` proving example (`ComponentsProbe`) was
promoted into a reusable `features/dashboard/useComponents.ts` hook + a real `DashboardPage.tsx`
rendering a semantic `<table>` (name + `StatusBadge` per component); `ComponentsProbe` deleted with
coverage preserved. This establishes the per-tab pattern (page + hook + per-feature MSW module) that
015c–015g copy.

### AC checklist (spec reviewer — all MET)
- **AC1** — fetches via `useComponents`→`apiClient`; semantic `<table>` with `<th scope="col">`,
  one row per component (name + StatusBadge dot+label). MET.
- **AC2** — loading / empty ("No components configured") / error+retry via shell primitives; all
  four paths (incl. success) driven via MSW; retry asserts `callCount==2`. MET.
- **AC3** — all five status→badge mappings asserted via accessible badge text scoped per-row,
  incl. the unknown-status guard. MET.
- **AC4** — `useComponents` extracted (discriminated-union state + cancelled-guard + attempt-keyed
  retry); `ComponentsProbe` fully deleted, no dead code; no `eslint-disable`; coverage net up. MET.

### API scope note
`ComponentDTO = {id, name, status}` only — verified at planning; the tab renders exactly that. The
"last-observed timestamp" originally in the draft AC was removed (no such field; a richer view needs
a backend DTO change → future story).

### DoD evidence — all gates green at `6d44c22` (clean committed tree)
Frontend: npm test 71 passed / 15 files; build exit 0; lint exit 0. Backend: lint-imports 5/0; ruff
check + format clean; pytest 426 (frontend-only diff). DB pair unaffected (no schema change).

### Reviews
- **Spec (Opus): PASS** — all 4 AC MET; ran the gates itself; traced each AC to a driving test.
- **Quality (Opus): APPROVE** — 0 Critical, 0 Major. Cancelled-guard intact (no race), tokens-only
  CSS, ink label text, coverage preserved across the ComponentsProbe deletion. One doc-only nit
  (stale `statusMapping.ts` docstring) folded in inline (`6d44c22`).

## Follow-ups captured (not blocking)
- **015c planning:** when the 2nd fetch hook lands, lift `useComponents` into a shared `useFetch<T>`
  (parallel-shape trigger) — flagged in `frontend-zone.md`. And a convention call on whether to
  double-test the retry path at both hook + page level.

## Wiki compile pass (blocking; complete)
`frontend-zone.md` updated for both stories (modular handlers, `cx`, catch-all, client hardening;
`useComponents` + real Dashboard; `ComponentsProbe` removed; `statusMapping` authoritative);
`code_refs` re-scoped (dead `handlers.ts` → `handlers/`). Mechanical sweep: 0 stale / 0 broken links
across 12 articles.

## Process metrics
- Reviewer rejections: 0 (both stories first-pass). Fix loops: 0. Hotfixes: 0. Blocked: 0.
- Estimate accuracy: 041 = 2 pts, 015b = 3 pts; no overrun. Commit cadence held (5 + 5 TDD commits).
- Velocity (if accepted): 5/5.
