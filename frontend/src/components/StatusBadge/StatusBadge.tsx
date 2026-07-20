import { cx } from '../../lib/cx'
import './StatusBadge.css'

/**
 * The 7-status health vocabulary (dossier status vocabulary -> health
 * mapping): operational->up, degraded_performance->degraded,
 * partial_outage->partial, major_outage->down, under_maintenance->
 * maintenance; `unknown`/`missing` cover no-data cases.
 */
export type HealthStatus =
  | 'up'
  | 'degraded'
  | 'partial'
  | 'down'
  | 'maintenance'
  | 'unknown'
  | 'missing'

export interface StatusBadgeProps {
  status: HealthStatus
  /** Overrides the default per-status label text. */
  label?: string
}

const DEFAULT_LABELS: Record<HealthStatus, string> = {
  up: 'Up',
  degraded: 'Degraded',
  partial: 'Partial outage',
  down: 'Down',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
  missing: 'Missing data',
}

/**
 * Pill health-status indicator (STORY-120 AC5). Status is NEVER conveyed by
 * color alone: a decorative dot (`aria-hidden`) carries the health color,
 * and a contrast-verified `-text` colored label always accompanies it — the
 * label is the accessible name, not the dot (tokens.contrast.test.ts proves
 * every `-text` on `-tint` pair meets WCAG AA).
 */
export function StatusBadge({ status, label }: StatusBadgeProps) {
  const text = label ?? DEFAULT_LABELS[status]

  return (
    <span className={cx('status-badge', `status-badge--${status}`)}>
      <span className="status-badge__dot" aria-hidden="true" />
      <span className="status-badge__label">{text}</span>
    </span>
  )
}
