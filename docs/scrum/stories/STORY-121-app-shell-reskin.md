# STORY-121 — App shell re-skin (collapsible sidebar + topbar, responsive)

**Status:** ready · **Points:** 3 · **Sprint:** 59
**As** an operator, **I want** the new app frame — grouped sidebar nav and a status-aware
topbar — **so that** I can move between the six sections and see overall system health from
anywhere, on any screen size.

## Context
Built on STORY-120's design system + Phosphor `Icon`. Reuses the existing six routes. Reference:
the approved prototype's shell. Skills mandatory (same five as STORY-120).

## Acceptance criteria
1. Sidebar shows three labelled groups — **Monitoring** (Dashboard, Availability, History),
   **Operations** (Approvals, Maintenance, Publications), **Pinned** (component quick-links) —
   each item a real router link (`<a>`/`<Link>`, keyboard-navigable) with a Phosphor icon.
2. The active route is visually indicated (`aria-current="page"` + styling). Approvals shows a
   pending-count badge sourced from the approvals endpoint (0 → no badge).
3. Topbar shows: page title, a worst-of **overall status pill** (dot + icon + text label —
   never colour alone), a last-updated indicator, and a notifications button (`aria-label`).
   A "＋ Maintenance" affordance is present.
4. Overall status is derived worst-of across components (down > partial > degraded >
   maintenance > unknown > up; empty → unknown). Unit-tested.
5. **Collapsible desktop sidebar (PO requirement 2026-07-21):** on ≥861px the sidebar toggles
   between an expanded state (icons + labels + group headings) and a narrow **icon-only rail**
   via a persistent toggle button (`aria-expanded`, `aria-controls`, `aria-label` reflecting
   the action). The choice **persists** across reloads (localStorage) and is restored without
   a flash of the wrong state (pre-paint or SSR-safe read). In the collapsed rail, each nav
   item still routes and shows an accessible **tooltip** with its label on hover/focus
   (emil delayed-tooltip pattern: initial delay, subsequent tooltips instant). The active
   route stays indicated in both states.
6. Responsive: at ≤860px the sidebar becomes an off-canvas **sheet** toggled by an
   `aria-expanded` button; **no horizontal scroll** at 375/768/1024/1440. (Desktop-collapse
   and mobile-sheet are distinct behaviours at their own breakpoints.)
7. **Motion (first-class — PO: "animations are important"):** the collapse/expand animates
   smoothly (label opacity+translate, width/rail transition) with an emil curve
   (`--ease-out`/`--ease-drawer`), ≤250 ms, interruptible; the mobile sheet slides from its
   edge with a backdrop fade and origin-correct transform. All motion animates
   `transform`/`opacity` (no `transition: all`), and is reduced/disabled under
   `prefers-reduced-motion` (state still changes, just without movement). Active-nav change and
   hover use subtle, consistent transitions. Verified in the reality gate (see below).
8. Focus-visible rings on all interactive elements; sheet dismissable by Escape and backdrop;
   focus returns to the toggle on close; rail toggle reachable and operable by keyboard.
9. Gates: `npm test`, `npm run build`, `npm run lint` exit 0.

## Reality gate
Live: shell renders on the running stack; the Approvals badge count equals
`GET /api/v1/approvals` length; overall pill matches worst-of `GET /api/v1/components`.
Collapse toggle flips expanded↔rail and **persists across reload**; collapsed rail shows
tooltips; mobile sheet opens/closes; scripted Chromium confirms the transition runs (and is
suppressed under emulated `prefers-reduced-motion: reduce`), zero console errors, no
horizontal scroll at 375/768/1024/1440. Since this is now a 3-pointer it gets **spec ∥ quality
reviews** in addition to the gate + reality gate.

## History
- 2026-07-21: `frontend/src/AppShell.tsx` + `AppShell.css` (STORY-120's minimal mount point —
  just enough to reach `/styleguide`) deleted and superseded by `frontend/src/shell/ShellLayout.tsx`
  (the real grouped-sidebar + topbar frame) plus a new `frontend/src/routes.tsx` routing table
  (a React Router layout route with `<Outlet />`, so `/styleguide` stays a standalone sibling
  route with its own `<h1>` rather than nesting inside the shell's topbar heading).
