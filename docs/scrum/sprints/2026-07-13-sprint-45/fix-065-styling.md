# STORY-065 — quality FIX brief (hand-back to the external implementer agent)

Spec review PASSED and all 9 DoD gate commands are green. The quality review raised **one MAJOR**
plus one folded-in minor. Fix these on branch `sprint-45`, keep the passing tests passing, then push
and tell the orchestrator to re-gate + re-review.

## MAJOR — styling-convention break in `frontend/src/pages/MaintenancePage.tsx`
The new `MaintenanceWindowRow` and the delete-error banner style static layout/spacing/color with
**~9 inline `style={{...}}` blocks**, and introduce **5 BEM className hooks that have no CSS
definition** (the diff never touched `MaintenancePage.css`):
`maintenance-window__row-content`, `maintenance-window__body`, `maintenance-window__reason`,
`maintenance-window__actions`, `maintenance-window-error`.

This breaks the established frontend convention: **per-page/component CSS files using design tokens**;
inline `style` is reserved for genuinely computed values only (the sole pre-existing inline style in
`src/pages` is AvailabilityPage's dynamic `width: ${width}%`). Nothing in these rows is computed.

**Fix:**
- Move every static inline style into `MaintenancePage.css`, defined under the already-named BEM
  class hooks above. Use the design tokens (CSS custom properties from `src/styles/tokens.css`) for
  spacing/color — not raw px/hex — matching the sibling pages (e.g. `DashboardPage.css`,
  `PublicationsPage.css`).
- Remove the inline `style={{...}}` props once the CSS covers them. Keep inline only if a value is
  truly dynamic (there are none here).
- No orphan class hooks: every `className` on these elements must have a matching rule in the CSS.

**Do not regress the passing tests:** the title must still render on the row as its own element
(distinct from `reason`), the inline two-step delete confirm (Delete → Yes/No, no `window.confirm`)
must still work, and the 404 path must still surface `role="alert"`.

## MINOR (fold in) — faithful MSW fixture actor
`frontend/src/mocks/handlers/publications.ts`: the author fixtures use invented values
`ops-admin` / `infra-bot`. The only actor the system emits today is `dashboard-operator`
(`frontend/src/api/actor.ts`). Change the present-author fixture(s) to `dashboard-operator` so the
mock is a faithful wire capture (keep one null-author row). Shape is already correct; this is
provenance, not a bug.

## When done
- Re-run the three frontend gates from `frontend/`: `npm test`, `npm run build`, `npm run lint`.
- Push to `sprint-45` and notify the orchestrator. The orchestrator will re-run the full DoD gate,
  re-review the styling delta, run the reality gate for both stories, then call the sprint review.
- STORY-066 already passed both reviews — no changes needed there.
