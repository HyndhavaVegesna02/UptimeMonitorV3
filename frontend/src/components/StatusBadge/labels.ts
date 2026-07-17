import type { HealthStatus } from './StatusBadge'

/**
 * The default per-status label text (STORY-100 quality-review fix): kept in
 * its own NON-COMPONENT module, not `StatusBadge.tsx` itself, so exporting
 * `defaultStatusLabel` (a plain function) alongside the `StatusBadge`
 * component doesn't trip the `react-refresh/only-export-components` lint
 * rule. `StatusBadge.tsx` imports `DEFAULT_LABELS` from here for its own
 * internal default label; `defaultStatusLabel` is re-exported through
 * `components/index.ts` for existing callers (e.g. the Approvals
 * confirm-step consequence copy, `features/approvals/ApprovalCard.tsx`) —
 * this stays the single source of truth for a status's default word rather
 * than a second copy.
 */
export const DEFAULT_LABELS: Record<HealthStatus, string> = {
  up: 'Up',
  down: 'Down',
  degraded: 'Degraded',
  partial: 'Partial outage',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
  missing: 'Missing data',
}

/**
 * The same default label text a bare `<StatusBadge status={status} />`
 * renders — exported so a caller that needs the WORD (not the badge markup)
 * reuses the SAME vocabulary rather than a second copy.
 */
export function defaultStatusLabel(status: HealthStatus): string {
  return DEFAULT_LABELS[status]
}
