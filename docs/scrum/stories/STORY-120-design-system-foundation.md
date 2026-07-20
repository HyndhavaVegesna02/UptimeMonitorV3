# STORY-120 — Design-system foundation + Phosphor icons

**Status:** ready · **Points:** 3 · **Sprint:** 59
**As** the team building the new frontend, **I want** a documented, three-layer design system
with Phosphor icons and core primitives **so that** every page is built from one consistent,
accessible, contrast-verified visual language matching the approved prototype.

## Context
Greenfield rebuild (PO 2026-07-21). Fresh `frontend/src`, keep only build toolchain. Visual
language = the approved refimg-derived system (`docs/scrum/sprints/2026-07-18-ui-prototyping/
round-2-refimg-system.md`) — reference, adapt with craft. Skills mandatory: ui-ux-pro-max,
web-design-guidelines, emil-design-eng, vercel-react-best-practices, design-system.

## Acceptance criteria
1. `@phosphor-icons/react` is a frontend dependency; a thin `Icon` wrapper pins default
   weight + size and requires either `aria-hidden` (decorative) or an accessible label. Test:
   decorative icons expose no accessible name; labelled icons do.
2. `frontend/src/styles/tokens.css` defines tokens in three layers (primitive → semantic →
   component). Light theme complete; token names are theme-scoped so a dark theme can be added
   without renaming. No component/primitive uses a raw hex — only `var(--…)`. Test/lint proves
   no raw hex in component CSS/TSX.
3. A token contrast test asserts every text-on-surface semantic pair meets **WCAG AA (≥4.5:1)**
   via computed relative luminance (parsed from `tokens.css`).
4. Type scale (Inter), 8px spacing scale, radius + shadow scale, and motion tokens (emil
   ease-out `cubic-bezier(.23,1,.32,1)`, ≤200 ms) exist as tokens and are used by primitives.
5. Core primitives exist with tests: Button, Card/Panel, StatusBadge (health chip),
   SummaryCard/KPI, Sparkline, LoadingState, ErrorState, EmptyState. Each renders
   hover/`:active`/`:focus-visible` affordances; any motion is `prefers-reduced-motion`-guarded
   and animates only `transform`/`opacity`.
6. A `/styleguide` route renders every primitive in all its states; it is reachable in the app
   and covered by a render test.
7. `docs/scrum/wiki/frontend-design-system.md` documents the system with `code_refs` +
   `verified_sha`.
8. Gates: `npm test`, `npm run build`, `npm run lint` all exit 0.

## Notes
Status vocabulary → health mapping: operational→up, degraded_performance→degraded,
partial_outage→partial, major_outage→down, under_maintenance→maintenance. Bright brand colours
are fills only; text uses darkened contrast-safe variants.
