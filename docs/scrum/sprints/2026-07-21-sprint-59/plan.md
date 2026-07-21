# Sprint 59 — New frontend: design system + shell + Dashboard (from the approved prototype)

**Goal:** Stand up a fresh, greenfield frontend on the approved *refimg*-derived visual
language — a documented design system (tokens + Phosphor icons + primitives), the re-skinned
app shell, and the full **Dashboard** page live on the real backend. One complete, demoable
vertical slice = the approved prototype, running on real data. The other five pages follow in
sprints 60–61.

**Mode:** in-process. **Branch:** `sprint-59` off `ui-prototype` (@280cac2). Merge back to
`ui-prototype` at review; **main is never touched** — PO acceptance at review *is* the swap.
**Reference (not a rigid spec):** `docs/scrum/sprints/2026-07-18-ui-prototyping/prototypes/refimg-dashboard.html`
+ derived system `…/round-2-refimg-system.md`. Adapt with craft; the prototype is a north
star, not a pixel contract.

## PO decisions (2026-07-21)

- **Greenfield, then swap.** Build fresh application code — do NOT evolve the rejected
  components. *Realization:* on `sprint-59` we rebuild all of `frontend/src/**` from scratch
  (new design system, new components, new pages, new API client). We keep only the **build
  toolchain** (`vite.config.ts`, `vitest`, `eslint.config.js`, `tsconfig*.json`, the
  `package.json` scripts) — toolchain is not design. The current app stays live on `main`
  until the PO accepts at review; that acceptance is the swap.
- **Sprint 59 = design system + shell + Dashboard** (~8 pts).
- **Light-first, dark-ready tokens.** Ship the light theme that matches the approved
  prototype; structure the token layer (primitive → semantic → component) so a dark theme is a
  later add, not a rewrite. No dark UI built this initiative unless requested.

## Non-negotiables (PO standing constraint)

Frontend only. **Do NOT modify** backend (`backend/**`), API contracts, `config/`, `infra/`,
DynamoDB, or the monitoring pipeline. The new API client is re-derived from the **live**
`/api/v1/*` contracts (verified against the running stack at the reality gate); the old
`frontend/src/api/types.ts` may be read *only* as a contract reference, not copied as UI.
No new Docker resources — reuse the existing local stack.

## Mandatory skills (baked into every story brief — PO: "it is a must")

Every implementer + reviewer brief carries the rules from all of these:
- **ui-ux-pro-max** — run its domain searches (`--domain style|ux|chart`) per story; its
  pre-delivery checklist is a gate item.
- **web-design-guidelines** — the Vercel web-interface-guidelines checklist (a11y, focus,
  forms, typography `…`/curly quotes/tabular-nums, content-handling, hover/state, dark-mode
  hooks). Run the skill's file review before each story's DoD.
- **emil-design-eng** — motion tokens & discipline: custom ease-out `cubic-bezier(.23,1,.32,1)`,
  ≤200 ms UI transitions, `:active` scale, `transform`/`opacity` only, `@starting-style`
  stagger, `prefers-reduced-motion` guards; no animation on keyboard-repeated actions.
- **vercel-react-best-practices** — React/Next perf rules now applicable (no waterfalls,
  bundle discipline, no inline component defs, derived-state-not-effect, uncontrolled inputs,
  `content-visibility`/virtualize long lists, resource hints).
- **design-system** — three-layer token architecture; no raw hex in component code; documented.

## Icons

**Phosphor Icons** (`@phosphor-icons/react`) replace the prototype's inline SVGs. Added as a
frontend dependency in STORY-120 (npm install — a frontend package, backend untouched). A thin
`Icon` wrapper pins default weight/size and enforces `aria-hidden` vs `aria-label` usage.

## Design system as an explicit deliverable

STORY-120 produces a **real, documented design system**, not just a stylesheet:
`frontend/src/styles/tokens.css` (three layers, light + dark-ready), a typography/spacing scale,
motion tokens, the Phosphor `Icon` wrapper, and a live **`/styleguide` gallery route** that
renders every primitive in all states — plus `docs/scrum/wiki/frontend-design-system.md`
(provenance-tracked). Contrast is enforced by a token test (WCAG-AA relative-luminance
assertions, as the prior system did).

## Execution order & steps

### 1. STORY-120 — Design-system foundation + Phosphor (3 pts)
Everything downstream depends on it; build and validate it first.
- [x] Step 1: fresh scaffold of `frontend/src` (clean out rejected src; keep toolchain
      config); wire `@phosphor-icons/react`; app boots with an empty shell + `/styleguide`.
- [x] Step 2: three-layer tokens (`tokens.css`) from the derived system — cool-grey canvas,
      single sky-blue accent, health palette, contrast-safe text tokens; light theme +
      dark-ready structure. Token contrast test (WCAG-AA) green.
- [x] Step 3: type scale (Inter), spacing (8px), radius/shadow, motion tokens (emil curves) +
      `prefers-reduced-motion` plumbing.
- [x] Step 4: `Icon` wrapper (Phosphor) + core primitives re-derived fresh: Button,
      Card/Panel, StatusBadge/health chip, KPI/SummaryCard, Sparkline, Loading/Error/Empty.
      Each with hover/active/focus-visible states per emil + web-guidelines.
- [x] Step 5: `/styleguide` gallery renders all primitives × states; tests per primitive.
- [x] Step 6: `frontend-design-system.md` wiki article (code_refs + verified_sha).
- [ ] Scoped DoD (`--only npm`); reviews spec ∥ quality (3-pointer).

### 2. STORY-121 — App shell re-skin, collapsible sidebar (3 pts)
The frame everything renders in. **Now a 3-pointer** (PO added a collapsible sidebar +
first-class motion, 2026-07-21) → gets the spec ∥ quality reviewer pair.
- [x] Step 1: grouped sidebar (Monitoring / Operations / Pinned) with Phosphor icons, active
      state, count badge; router wired to the six existing routes.
- [x] Step 2: **collapsible desktop sidebar (PO requirement)** — toggle between expanded and a
      narrow icon-only rail, persisted (localStorage, no wrong-state flash), tooltips on rail
      items (emil delayed-tooltip pattern), active route indicated in both states.
- [x] Step 3: topbar — page title + worst-of overall status pill (dot+icon+label, never colour
      alone), last-updated, notifications button; "＋ Maintenance" action affordance.
- [x] Step 4: responsive — off-canvas **sheet** ≤860px (distinct from desktop rail),
      no horizontal scroll 375/768/1024/1440; keyboard-navigable; Escape/backdrop dismiss.
- [x] Step 5: **motion polish** (see "Motion is first-class" below) — collapse/expand + sheet
      transitions, reduced-motion guards; verified in reality gate.
- [ ] Scoped DoD; reviews spec ∥ quality (3-pointer) + reality gate.

### 3. STORY-122 — Dashboard page on real data (3 pts)
Highest-value page; exercises the most primitives → validates the system end-to-end.
- [x] Step 1: fresh API client methods for the endpoints the page needs (components, history,
      approvals, maintenance, sample-mode), typed from the live contracts.
- [ ] Step 2: KPI row (availability, avg latency, components healthy, pending approvals) with
      inline SVG sparklines; derived, not invented.
- [ ] Step 3: response-time chart (inline SVG, periodic-refresh visuals per ui-ux-pro-max
      chart domain — no ticker), probe-locations panel (segmented control), upcoming-maintenance.
- [ ] Step 4: recent-checks feed + components roster; worst-of overall-status derivation.
- [ ] Step 5: per-region loading / error / empty states (reduced-motion guarded); suite green.
- [ ] Step 6: reality gate (ui-sweep + live API): every rendered number cross-checked vs
      `/api/v1` truth, both mobile/desktop, zero console errors.
- [ ] Scoped DoD; reviews spec ∥ quality (3-pointer).

**Scope:** 120(3) + 121(3) + 122(3) = **9 pts** (velocity ref: recent 4–8/sprint; slightly
on the fuller side after the PO added the collapsible sidebar + motion scope to 121).

## Motion is first-class (PO: "animations are important", 2026-07-21)

Motion is a graded deliverable this sprint, not a nicety. All of it follows emil-design-eng:
- Motion tokens live in `tokens.css` (STORY-120): `--ease-out: cubic-bezier(.23,1,.32,1)`,
  `--ease-in-out: cubic-bezier(.77,0,.175,1)`, `--ease-drawer: cubic-bezier(.32,.72,0,1)`, and
  duration tokens (press 120–160 / control 150–200 / drawer 200–250 ms).
- Only `transform`/`opacity` animate; never `transition: all`; exits faster than enters;
  `@starting-style`/stagger for list/section entrance (30–80 ms steps); `:active` press-scale
  on pressables; origin-aware popovers/tooltips; interruptible transitions.
- The sidebar collapse/expand and the mobile sheet are the sprint's signature motions
  (STORY-121). Chart/data entrance is gentle and one-shot; **no motion on data refresh or
  keyboard-repeated actions**.
- Every animation is guarded by `prefers-reduced-motion` (state still changes; movement is
  removed). The reality gate emulates `reduce` and asserts motion is suppressed.
- Reviewers (quality) explicitly check motion against the emil checklist; the web-guidelines
  animation rules are a gate item.

## Plan-verifier

**SKIPPED** (token economy, PO-approved 2026-07-15). Not contract-sensitive: all three stories
are UI rendering against the **existing, live-verified** `/api/v1` contracts (the same ones the
deployed app already consumes); no adapter/vendor path, no units/scale logic, in-process mode.
The per-story **reality gate** (live render-vs-wire vs the running stack) covers contract
consumption. Skip + reason recorded here for PO visibility at approval.

## Gates

- **Mid-sprint:** scoped `python .claude/skills/yourteam/scripts/yt_gate.py --only npm`
  (frontend diff only touches npm-gated commands; backend commands stay green untouched).
- **Sprint close:** full 8-command gate on final HEAD is the evidence of record (pytest,
  import-linter, ruff check, ruff format, cfn-lint, npm test, npm build, npm lint) — all must
  be exit 0. Gate shells run with `DYNAMO_ENDPOINT_URL` UNSET (retro-52 A1).
- **Reality gate:** local stack up (DynamoDB Local 8001, API 8000, loop, Vite 5173); scripted
  Chromium (`tools/ui-sweep`) cross-checks the UI against live API truth.

## Sprint close → review

Full gate → wiki compile pass → journal → delegated spec ∥ quality reviews on the 3-pointers →
present to PO. **Do not merge to main** — PO decides the swap at review.
