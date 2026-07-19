# Sprint 59 - Signal Field foundation

## Goal

Replace the existing frontend visual foundation with a distinctive, accessible Signal Field language while preserving the entire backend contract and all six routes.

## Design read

This is a product workspace for operators who need composure and orientation during incidents. The visual direction is a dense signal field: restrained surfaces, strong editorial hierarchy, information bands, and precise state color. It deliberately avoids the generic dashboard reflex of equal cards, decorative charts, or a default dark SaaS skin.

- Design variance: 7/10. The shell and route layouts use deliberate asymmetry and recurring structural bands, then collapse to a strict single-column mobile layout.
- Motion intensity: 3/10. Only feedback and state transitions animate. Reduced motion removes those transitions.
- Visual density: 8/10. Data stays compact with tabular numerals and clear grouping, never fabricated metrics.

## Scope

| Story | Points | Pipeline | Scope |
| --- | ---: | --- | --- |
| STORY-111 | 5 | full | Token system, documented design language, Phosphor icon migration, and shared primitives. |

Plan-verifier: skipped. This is a pure frontend UI story consuming existing, verified DTOs with no backend or vendor contract change.

## Verified constraints

- Work is confined to `frontend/` plus rewrite documentation and Scrum records.
- Routes remain `/`, `/availability`, `/approvals`, `/check-history`, `/maintenance`, and `/publications`.
- `frontend/src/api/client.ts` and `frontend/src/api/types.ts` remain wire-compatible with the existing FastAPI endpoints.
- Light and dark themes, keyboard operation, semantic controls, status text, and reduced-motion support are retained.
- `@phosphor-icons/react` is the required icon source.
- The prior `ui-rewrite` branch is read-only reference material and is never merged or modified.

## STORY-111 plan

- [ ] Write focused failing tests for theme token behavior, the Phosphor-backed icon API, and representative primitive states.
- [ ] Add the Phosphor dependency and replace the handwritten icon catalogue with a typed, accessible adapter.
- [ ] Define the Signal Field token layers and global typography, interaction, responsive, and reduced-motion rules.
- [ ] Write `DESIGN.md` as the implementation contract for the clean-slate visual language.
- [ ] Rebuild the shared primitives against the new tokens without changing the API client or route definitions.
- [ ] Adapt focused route-shell styling only as needed to exercise the new primitives, preserving route behavior.
- [ ] Run frontend tests, build, lint, a visual render check in both themes, and the empty-backend-diff check.
- [ ] Commit the green story, record evidence, and update the frontend wiki blast radius.

## Reality gate

Run the frontend locally against the existing API seam. Verify the shell and a representative primitive state in both themes at desktop and 390px widths, with reduced motion enabled. Confirm the browser makes no requests outside the established `/api/v1/*` endpoints.
