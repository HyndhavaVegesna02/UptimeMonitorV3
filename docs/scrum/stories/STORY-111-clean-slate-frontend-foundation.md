---
id: STORY-111
title: Clean-slate frontend foundation - distinct signal-field design system, themes, Phosphor icons, and shared primitives
type: feature
---

## Context

The PO requested a clean-slate rewrite on `ui-rewrite-codex`, cut directly from `main`, with no backend changes and no reuse of the pre-existing `ui-rewrite` branch. The current operator SPA has six working routes and a verified typed API seam. Its visual system may be replaced, but the routes, client contracts, and existing actions must remain.

## Description

Create the visual and component foundation for a distinctive, dense operator workspace called the Signal Field. It should use a disciplined light and dark theme, Phosphor icons, reusable primitives, and a documented design language that the six route rewrites can consume. This is a foundation story only: it does not change backend functionality or invent any API-driven data.

## Acceptance Criteria

- [ ] AC1: The frontend has a documented Signal Field design system in `DESIGN.md`, including visual intent, semantic tokens, type scale, component rules, responsive behavior, and reduced-motion behavior for both themes.
- [ ] AC2: `frontend/src/styles/` exposes a complete token layer for the new light and dark themes. Components use semantic tokens rather than page-local color values.
- [ ] AC3: The application uses `@phosphor-icons/react` for visible UI icons; the handwritten SVG icon catalogue is removed or reduced to a compatibility-free absence. The existing routes and accessible names remain intact.
- [ ] AC4: Shared primitives needed by subsequent routes are rebuilt in the new visual language with explicit loading, empty, error, focus, disabled, and responsive states where applicable. They retain semantic HTML and status text in addition to color.
- [ ] AC5: The typed API client and backend-facing DTOs are unchanged, and `git diff sprint-59-start..HEAD -- backend/ config/ infra/ scripts/ pyproject.toml` is empty.
- [ ] AC6: Focus-visible, light and dark theme selection, and reduced-motion behavior are covered by focused frontend tests; `npm test`, `npm run build`, and `npm run lint` pass.

## Open Questions

None. The PO confirmed the six-route IA and existing backend functionality must stay intact, Aura is optional inspiration only, and the redesign must avoid a generic dashboard result.

## History

- 2026-07-19: drafted and approved under the PO's delegated clean-slate rewrite initiative.
