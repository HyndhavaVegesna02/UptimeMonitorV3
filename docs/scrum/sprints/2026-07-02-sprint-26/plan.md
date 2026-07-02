# Sprint 26 — Plan

**Dates:** starts 2026-07-02.
**Goal:** land the first real frontend tab (015b Dashboard) on a hardened shell (041 first).
**Branch:** `sprint-26` (tag `sprint-26-start` @ `9e9b369`). Committed: 5 pts (041=2 + 015b=3; velocity mean 4.33).
**Mode:** in-process — Sonnet 5 implementer subagent at high effort (PO directive 2026-07-02); Opus reviewers.
**Execution order:** STORY-041 → STORY-015b (041 hardens the shared seams 015b + all later tabs build on).

All work is inside `frontend/`. **No backend source change.** The six backend DoD commands must stay
green untouched; the three frontend commands (`npm test` / `npm run build` / `npm run lint`, run from
`frontend/`) must all exit 0 on a clean committed tree. Design reference: `DESIGN-linear.app.md` (guide);
the shell's existing token layer + primitives are the vocabulary — reuse them, add no new raw hex.

TDD cadence: failing test → see it fail → minimal code → green → **commit after every green step**,
staging only touched files (never `git add -A`), branch verified `sprint-26` before each commit.

---

## STORY-041 — Frontend pattern hardening (2 pts) — do FIRST

Chore from the STORY-015a quality review: tighten the shell seams before six tabs copy them. Files:
`frontend/src/api/client.ts`, `frontend/src/components/Button/Button.tsx` +
`components/Panel/Panel.tsx` (+ a new `cx` helper), `frontend/src/mocks/handlers.ts`,
`frontend/src/AppShell.tsx`.

- [x] **T1 — Typed error on malformed 2xx body (AC1).** In `client.ts::getJson`, the
      `await response.json()` on a 2xx with an invalid body currently throws a raw `SyntaxError`
      that escapes unwrapped. Wrap it: on a JSON-parse failure, throw `ApiError` (message names the
      path; carry the status). Test (Vitest + MSW): a handler returns 200 with a non-JSON body →
      assert the client rejects with `ApiError` (not a bare `SyntaxError`). Keep the existing
      network-error and non-2xx behavior unchanged (their tests stay green).
- [x] **T2 — Shared `cx()` classnames helper (AC2).** Add `frontend/src/lib/cx.ts` (or
      `components/cx.ts` — match where shared UI utils naturally sit): `cx(...parts): string` that
      filters falsy and joins on a space — exactly the `[...].filter(Boolean).join(' ')` idiom
      duplicated in `Button.tsx` and `Panel.tsx`. Unit-test it (falsy filtering, empty → ''). Then
      replace the inline idiom in `Button.tsx` and `Panel.tsx` with `cx(...)`; their existing tests
      must stay green (behavior identical). No new raw hex; tokens unchanged.
- [x] **T3 — Per-feature MSW handler modules (AC3).** Refactor `mocks/handlers.ts` so handlers
      compose from per-feature modules instead of one flat array + one fixture export: e.g.
      `mocks/handlers/components.ts` exporting its handlers (+ `FIXTURE_COMPONENTS`), and
      `mocks/handlers/index.ts` spreading them into the `handlers` array the server registers
      (`mocks/server.ts` keeps importing `{ handlers }`). Goal: a future tab story adds
      `mocks/handlers/<feature>.ts` + composes it, touching no other feature's handlers. Existing
      tests that `server.use(...)` or import `FIXTURE_COMPONENTS` must keep working (re-export as
      needed). The full suite stays green.
- [x] **T4 — Catch-all route (AC4).** In `AppShell.tsx` add a trailing `<Route path="*" ...>`
      rendering a small "not found" panel (use the shell's `Panel`/`EmptyState` + a link back to
      Dashboard) — an unknown path currently renders Nav + an empty `<main>`. RTL test: navigating
      (MemoryRouter) to an unknown path renders the not-found content and the Nav still shows.
- [x] **T5 — Gates green (AC5).** `npm test`, `npm run build`, `npm run lint` all exit 0 on a clean
      committed tree. No CLAUDE.md/DoD change (no command added). No wiki blast radius expected
      (041 touches no file in any article's `code_refs` except possibly `frontend/package.json` — it
      shouldn't; flag if it does).

**041 conventions:** tokens-not-hex; tests drive real behavior (MSW is the only mock; never mock the
unit under test); a refactor (T2/T3) REWRITES/keeps the covering tests green — never deletes coverage;
scoped staging; no `eslint-disable` to silence a real defect; TS strict stays on.

---

## STORY-015b — Dashboard tab (3 pts) — do SECOND, on the hardened shell

Promote the shell's `GET /api/v1/components` proving example into the real Dashboard tab. API contract
(VERIFIED 2026-07-02): `backend/src/api/v1/components/models.py::ComponentDTO` = `{id, name, status}`
ONLY — no timestamp/latency/location. Render only what the DTO provides (name + status badge). The
shell already wired the endpoint in `features/dashboard/ComponentsProbe.tsx`; 015b extracts + promotes it.

- [x] **T1 — Extract `useComponents` hook (AC4).** Move the fetch logic out of `ComponentsProbe.tsx`
      into `frontend/src/features/dashboard/useComponents.ts`: the discriminated-union `FetchState`
      (`loading | error | success`), the cancelled-guarded effect, and the `attempt`-keyed `retry`
      callback (mirror the existing ComponentsProbe implementation exactly — it's already race-safe
      and eslint-clean). Return `{ state, retry }`. Unit-test the hook via a component that renders
      its states, driving success + error→retry against MSW (assert refetch, e.g. via call count or
      the success content appearing after a 500). No `eslint-disable`.
- [x] **T2 — Real DashboardPage (AC1, AC2).** Rewrite `frontend/src/pages/DashboardPage.tsx` to use
      `useComponents` and render a semantic table (`<table>` with `<th scope="col">` for Component /
      Status) — one row per component: name + `<StatusBadge status={toHealthStatus(c.status)} />`.
      Panel `headingLevel="h1"` (top-level tab). Wire loading (`LoadingState`), empty
      (`EmptyState` — "No components configured"), and error+retry (`ErrorState`) via the hook's
      state. Remove the placeholder copy ("Live health overview lands in STORY-015b") and the
      "Backend connectivity check" scaffolding.
- [x] **T3 — Remove ComponentsProbe scaffolding (AC4).** Delete `features/dashboard/ComponentsProbe.tsx`
      + its `.css` + test once the hook + page cover their behavior (the covering tests are REWRITTEN
      onto `useComponents`/`DashboardPage`, not dropped — 2026-06-29 agreement). No dead code, no
      orphan CSS/imports. `statusMapping.ts` stays (now consumed by the real page).
- [x] **T4 — Status→badge mapping test (AC3).** Test each mapping via accessible badge text:
      operational→UP, degraded→DEGRADED, partial_outage→DEGRADED, major_outage→DOWN, and an
      unrecognized status → the neutral "unknown" badge (the `toHealthStatus` `?? 'unknown'` guard).
      Drive it through the rendered Dashboard (MSW fixture with the range of statuses), asserting the
      badges' accessible labels — not by calling `toHealthStatus` in isolation only.
- [x] **T5 — MSW handlers + gates (AC2, AC5).** Add/extend the components handler in the per-feature
      module from 041-T3 with fixtures covering the success (multiple statuses), empty (`[]`), and
      error (500) cases used by the tests. All three frontend gates exit 0 on a clean committed tree.

**015b conventions checklist (held at quality review):**
- Tokens-not-hex; status is dot/icon + ink label, never color-alone; health color never as text color
  (label text = ink tokens ≥4.5:1 both themes — the badge dot/background carries the health color).
- **Empty-input tested:** the `[]` → "no components" empty state has a driving MSW test (2026-06-25).
- **Tests drive real behavior:** MSW at the network boundary is the only mock; never mock `useComponents`
  or the page under assertion; assert via table roles / accessible badge text, not implementation details
  (2026-06-29 assembly-test agreement, frontend edition).
- **Contract change rewrites tests:** the ComponentsProbe tests become useComponents/DashboardPage tests;
  no net coverage loss for the fetch/status-mapping behavior (2026-06-29).
- **Per-tab pattern for 015c–015g:** page in `pages/` + fetch hook in `features/<tab>/` + per-feature MSW
  module — this is the template the later tabs copy; keep it clean and self-contained.
- Scoped staging; commit-after-green; TS strict on; no `eslint-disable`; module/exported-symbol comments
  where a new public hook/util is introduced (mirror the shell's existing doc-comment style).

---

## Guardrails (implementer)
- Build to THIS plan + the story AC (`docs/scrum/stories/STORY-041-*.md`, `STORY-015b-*.md`) + dossier §17 —
  never to chat history. Do 041 fully (all gates green, committed) before starting 015b.
- Do NOT change backend source; the six backend gates must stay green. Do NOT write `.scrum/` board state;
  do NOT run reviewers or merge — the orchestrator owns the back half.
- Genuine ambiguity → STOP and report the exact question. Effort > 3× a story's estimate → STOP and report.
- Report per-story: steps done + commit SHA each; every gate command + exit code + tail; wiki articles
  touched/flagged; anything noticed-but-not-done; or the blocking question.

## Sequencing rationale
041 before 015b: 041 hardens the shared client/handlers/primitives (the blast-radius seam every tab
touches); doing it first means 015b — and by extension the 015c–015g template — is built on the clean
version, avoiding rework. Within each story, steps are dependency-ordered (helper/hook before the
consumers; gates last). 015b is the higher-uncertainty story (first real tab, sets the pattern) but
depends on 041, so 041's low-risk hardening lands first and 015b gets the bulk of the runway.
