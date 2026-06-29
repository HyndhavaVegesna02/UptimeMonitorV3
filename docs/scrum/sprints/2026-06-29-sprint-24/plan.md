# Sprint 24 — Plan

**Goal.** Ship the first real frontend tab — the **Dashboard** (component statuses) — on the STORY-015a
shell, establishing the **per-tab pattern** every later tab (015c–015g) will copy: a dedicated page
component + a data hook + a `DESIGN-airtable.md`-styled layout + loading/empty/error states + MSW-backed
Vitest tests.

**Single story: STORY-015b (3 pts).** Pipeline: `external impl + Opus spec & quality reviewers + frontend DoD gate`.

## Baseline
- Branch `sprint-24` cut from `main` @ `cd015ab` (sprint-23 merged). `start_tag`: `sprint-24-start`.
- The shell (STORY-015a) already wired `GET /api/v1/components` as the Dashboard proving example, with a
  `getStatusBadge` helper and the four health tokens in `frontend/src/index.css`. This story PROMOTES that
  into a polished, extracted, fully-tested Dashboard tab.

## Design source
`DESIGN-airtable.md` (repo root) is the binding visual design — reuse the shell's token layer and the four
health tokens (`--colors-health-up/down/degraded/maintenance` + `--colors-health-down-surface`). Editorial→
dashboard adaptation still holds: canvas/hairline surfaces, `body-md`/`label-md` type, modest weights, no
marketing chrome, no `:hover` styling (no-hover policy). See the `frontend-zone` wiki article.

## The endpoint (already exists — no backend change)
`GET /api/v1/components` → `list[ComponentDTO]` where `ComponentDTO = { id: string, name: string, status:
string }` (`backend/src/api/v1/components/`). `status` is one of up / down / degraded / maintenance (map to
the health tokens; treat any unknown value defensively — show it as neutral + the raw string, do not crash).

## Tasks (TDD; commit after each green step; scoped staging — never `git add -A`)

### T1 — Extract a Dashboard page + a data hook  *(refactor; folds in the Sprint-23 carry-forward)*
- Move the Dashboard rendering out of `App.tsx` into its own component, e.g. `frontend/src/tabs/Dashboard.tsx`
  (pick a consistent `tabs/` or `pages/` folder — this is the pattern the other tabs follow).
- Extract the fetch into a small data hook, e.g. `frontend/src/hooks/useComponents.ts`, returning
  `{ data, loading, error, refetch }`. This REMOVES the `eslint-disable react-hooks/set-state-in-effect`
  smell from the shell (Sprint-23 open minor) — the hook owns the effect cleanly (fetch on mount, expose
  refetch; no setState-in-effect-on-prop-change pattern).
- `App.tsx` now just renders `<Dashboard />` for the dashboard route; the other five tabs keep their
  placeholders. Keep the existing apiClient seam (`fetchComponents`).

### T2 — Dashboard layout, styled from DESIGN-airtable.md  *(AC1)*
- Render each component as a status card or table row (implementer's choice — pick what reads cleanest for a
  data-dense cockpit; cards in a responsive grid, or a hairline-divided list/table). Each item shows the
  component name (`label-md`/`title-sm`) + its status as the existing health badge (status dot/icon + text
  label — SVG, never color alone). Use the token vars only; NO raw hex in components.
- A header/title for the tab; comfortable spacing on the 4px/section rhythm; responsive (no horizontal
  scroll at 375px; cards reflow / table stays readable).

### T3 — States: loading, empty, error+retry  *(AC2)*
- Loading: a skeleton or calm "Loading…" panel (per the design's quiet aesthetic), not a jarring spinner.
- Empty (`[]` from the API): a helpful empty state ("No components configured yet" + neutral styling), NOT
  a blank screen.
- Error: the error panel + a "Try Again" that calls the hook's `refetch` (reuse/upgrade the shell's pattern;
  keep the tokenized `--colors-health-down-surface` tint — no raw literals).

### T4 — Tests (Vitest + RTL + MSW)  *(AC2; real-component tests)*
- Move/expand the Dashboard tests into the new component's test file (e.g. `Dashboard.test.tsx`). Render the
  REAL `<Dashboard />` (or `<App />` routed to it); MSW mocks only the network edge. Cover:
  - success → renders all components with the correct health badge per status (assert the up/down/degraded/
    maintenance mapping, e.g. via accessible label/text, not the color);
  - empty → the empty state renders;
  - error (MSW 500) → the error panel + retry recovers after a handler reset.
- Keep the shell's six-tab nav/routing test green (in `App.test.tsx`) — if you move Dashboard assertions
  out, leave the nav/routing assertions intact.

### T5 — Accessibility + responsive pass  *(AC3)*
- Status conveyed by icon+label (already), contrast ≥4.5:1, the list/table is keyboard-reachable and
  screen-reader sensible (a table uses real `<table>`/`<th scope>`; cards use a list/`<ul>` or headings).
  No horizontal scroll at 375px. Respect the a11y floor from `ui-ux-pro-max` (UX floor only).

## Conventions checklist (held at quality review)
- **vercel-react-best-practices:** no components-inside-components; derive during render (don't mirror props
  in effects); the data hook owns its effect with narrow deps; stable list keys (component `id`); explicit
  conditional rendering for the loading/empty/error/success branches.
- **Real-component tests** (RTL renders the real Dashboard; MSW mocks only the network edge) — no asserting
  what you mocked.
- **DESIGN-airtable.md fidelity** — token vars only, the four health tokens, no marketing chrome, no
  `:hover`. **No raw hex/rgba in components** (the token/class layer is the only home for literals).
- **Empty + error + loading** all present and tested; **clean committed tree** (commit any prettier/eslint
  --fix output in the same step); **scoped staging**, never `git add -A`.
- **Scaffold-hygiene (2026-06-29):** N/A — no generator is run this sprint; do not introduce new boilerplate.
- **Command-sync:** no command change expected; touch CLAUDE.md only if one changes.

## DoD gate
- **Frontend gate (run from `frontend/`), all exit 0 on a CLEAN committed tree:** `npm run typecheck` ·
  `npm run lint` · `npm run test` · `npm run build`.
- **Python six-command gate must stay green** (no backend change expected — confirm).

## Guardrails for the implementer
Build to THIS plan + the STORY-015b AC + `DESIGN-airtable.md` + the existing shell code (reuse the token
layer, the health badges, the apiClient seam). This is ONE tab — the Dashboard; the other five stay
placeholders (their bodies are 015c–015g). Do NOT touch the Python backend. Do NOT write `.scrum/` board
state. Do NOT run the reviewers or merge. Stop-and-report on genuine ambiguity or a 3× effort overrun.
