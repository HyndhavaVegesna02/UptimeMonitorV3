# Sprint 25 — Plan

**Dates:** starts 2026-07-02.
**Goal:** rebuild the frontend zone from scratch — the shell (STORY-015a) — guided by
`DESIGN-linear.app.md`, with dark + light themes, so tabs 015b–015g become pure fill-ins.
**Branch:** `sprint-25` (tag `sprint-25-start` @ `521764c`). Committed: 5 pts (velocity mean 4.33 — single-story focused sprint).
**Mode:** in-process implementation (PO directive 2026-07-02, superseding the 2026-06-26
external-handoff agreement) — a **Sonnet 5 implementer subagent at high effort** builds THIS
plan + the story file + the dossier §17; the orchestrator runs the gate + Opus reviewers +
review back half.

Context: the first frontend (sprints 23–24, DESIGN-airtable.md) was fully reverted in `521764c`.
This is a fresh build — do NOT resurrect code from the `sprint-23`/`sprint-24` branches; the
design direction changed (Linear-guided, dark+light). Story file:
`docs/scrum/stories/STORY-015a-frontend-shell.md` (AC1–AC7 are the contract of record).

## Design brief (binding for this sprint)

`DESIGN-linear.app.md` (repo root) is a **guide, not a copy target** — adopt its language,
adapt it to a data-dense operator cockpit:

- **Surfaces:** canvas → surface-1..4 ladder + hairline borders carry ALL hierarchy. No drop
  shadows. Panels: surface-1, 1px hairline, 12px radius. Controls: 8px radius.
- **Accent discipline:** lavender `#5e6ad2` (hover `#828fff`, focus `#5e69d1`) ONLY on:
  primary button, focus rings, active-tab indicator, links. Never as a surface fill, never
  decorative. No second chromatic accent outside the health palette.
- **Type:** Inter 400/500/600 (self-hosted/@fontsource; no runtime font CDN). Headings ≤28px,
  weight 600, negative tracking (≈ -0.6px at 28px, tapering to 0 at body). Body 14–16px/1.5.
  JetBrains Mono for machine values (IDs, timestamps, latencies). No 40px+ marketing display type.
- **Dark theme (default when the OS prefers dark):** canvas `#010102`; surfaces `#0f1011`,
  `#141516`, `#18191a`, `#191a1b`; hairlines `#23252a` / `#34343a`; ink `#f7f8f8` / `#d0d6e0` /
  `#8a8f98` / `#62666d`.
- **Light theme:** canvas `#ffffff`; surfaces from the reference's inverse tokens (`#f5f6f6`,
  `#f6f7f7`, then two designed steps); designed hairline/ink equivalents (keep the same
  4-step ink hierarchy; every ink-on-surface pair ≥4.5:1). Same accent lavender.
- **Health tokens (BOTH themes; committed in the token layer; reused by every tab):**
  `up` green, `down` red, `degraded` amber, `maintenance` blue (clearly distinct from the
  lavender accent), each with a `-subtle` surface variant for badge backgrounds. Suggested
  starting values — dark: up `#27a644`, down `#e5484d`, degraded `#d5a021`, maintenance
  `#3b9eff`; light: up `#1a7f37`, down `#c53030`, degraded `#9a6700`, maintenance `#0b68cb`.
  Tune freely, but hold the floor: non-text cues ≥3:1 against their surface; **health color is
  never text color and never the sole carrier of status** (dot/icon + ink label, always).
- **Skills lanes:** `ui-ux-pro-max` = a11y/UX floor only (do NOT generate a design system with
  it); `web-design-guidelines` = final audit; `vercel-react-best-practices` = React patterns.

## STORY-015a — Frontend shell (5 pts) — AC1–AC7

Toolchain (locked): Vite + React + TS strict SPA in `frontend/`, npm, Vitest + RTL + MSW,
ESLint. Playwright deferred. Vite dev proxy `/api` → local backend; CORS stays deferred to
STORY-017. No backend source changes.

TDD cadence: write the failing test, see it fail, minimal code, see it pass, **commit after
every green step**, staging only the files you touched (never `git add -A`).

- [ ] **T1 — Scaffold + hygiene (AC1).** `npm create vite@latest frontend` (react-ts), enable
      TS strict, add Vitest + RTL + jsdom + MSW + ESLint. PRUNE generator boilerplate: template
      SVGs/logos, template favicon (replace with a minimal project one), default `<title>`
      (set a real app title), boilerplate CSS/README content. Configure the `/api` dev proxy.
      Prove `npm run build`, `npm test`, `npm run lint` all exit 0 on the clean scaffold.
- [ ] **T2 — Token layer + themes (AC4 foundation, AC5).** `src/styles/tokens.css` (or
      equivalent): CSS custom properties per theme under `:root[data-theme="dark"]` /
      `:root[data-theme="light"]` — surfaces, hairlines, ink scale, accent set, health set
      (+subtle variants), radii, spacing (4px base), type scale + families (Inter,
      JetBrains Mono via @fontsource). Inline pre-paint script resolves theme: localStorage
      override → else `prefers-color-scheme`. Theme toggle hook + persistence. Tests:
      system-default resolution, toggle override, persistence (AC5).
- [ ] **T3 — Shell primitives (AC4).** `src/components/`: `Button` (primary/secondary/
      tertiary per the reference specs — 8px radius, compact padding), `StatusBadge` (pill,
      surface bg, status dot + ink label; accepts up/down/degraded/maintenance/unknown),
      `Panel`, `LoadingState`, `ErrorState` (with retry callback), `EmptyState`. Tokens only —
      zero raw hex in any component. RTL tests: badge renders dot + accessible label per
      status; unknown → neutral.
- [ ] **T4 — Nav + routing (AC2).** Router with six routes; top nav (56px, canvas bg, hairline
      bottom): app title left, six tabs (Dashboard · Availability · Approvals · Check History ·
      Maintenance · Publications), theme toggle right. Active tab: ink + accent indicator;
      inactive: ink-subtle; keyboard operable, visible accent focus ring, ≥40px targets.
      Placeholder panel per tab. RTL test: six nav items render; clicking (and keyboard)
      switches the active panel (AC2).
- [ ] **T5 — Typed API client + proven endpoint (AC3).** `src/api/client.ts`: fetch-based,
      single base-URL seam (`/api`), typed DTOs matching the backend (`GET /api/v1/health` or
      `GET /api/v1/components` — DTO shapes in `backend/src/api/v1/*/models.py`). MSW server
      setup for tests. Wire the endpoint into a placeholder with loading / error / retry.
      Tests: success path renders data; error path shows ErrorState; retry refetches (MSW).
- [ ] **T6 — A11y pass (AC6).** Sweep both themes against the `ui-ux-pro-max` a11y floor +
      `web-design-guidelines`: text contrast ≥4.5:1 every ink/surface pair, focus visible on
      every interactive element, no color-only status, targets ≥40px. Fix and test what the
      sweep finds.
- [ ] **T7 — Gates + doc sync (AC7).** Activate the three frontend commands in
      `.scrum/definition-of-done.md` (replace the "placeholder until then" note) and add the
      frontend section to CLAUDE.md (commands, `frontend/` layout, design-reference pointer)
      **in the same commit** (command-sync agreement). Final full run: three frontend gates +
      six backend gates all exit 0 on a clean committed tree.

## Conventions checklist (all new code is held to this at review)

1. **Tokens, not hex:** no raw color/size literals in components; everything references the
   token layer. (The token file itself is the only place hex lives.)
2. **Status is never color-alone**; health tokens never used as text color; label text = ink
   tokens at ≥4.5:1 in BOTH themes.
3. **Tests drive real behavior** — never patch/mock the thing under assertion (2026-06-29
   assembly-test agreement, frontend edition: don't mock a component/hook to test it; mock
   only the genuine I/O edge, which is MSW at the network boundary). Assert via accessible
   roles/text, not implementation details.
4. **A contract change rewrites its tests** — never delete a covering test into a coverage gap
   (2026-06-29 agreement).
5. **Empty-input behavior:** every list-rendering surface has an explicit tested empty state
   (2026-06-25 agreement, frontend edition).
6. **Scoped staging; commit-after-green; TS strict stays on; no `eslint-disable` to silence a
   real defect.**
7. **CLAUDE.md + DoD sync in the same commit as the gate change** (T7).
8. **No backend source changes.** The six backend gates must remain green untouched.

## Guardrails (implementer)

- Build to THIS plan + the story AC + dossier §17 — never to chat history.
- Do NOT write `.scrum/` board state; do NOT run reviewers or merge; the orchestrator owns the
  back half.
- Genuine ambiguity → stop and report the exact question; do not guess.
- Effort > 3× the estimate → stop and report what was tried.

## Sequencing rationale

Single story; T1→T7 ordered by dependency (tokens before components before nav/client, gates
last so the doc-sync commit captures the final command set). Highest-risk item (the two-theme
token layer, new since the reverted attempt) lands second, immediately after the scaffold,
so a problem there surfaces with maximum runway.
