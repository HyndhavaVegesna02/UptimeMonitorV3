import './StatusBadge.css'

export type HealthStatus =
  | 'up'
  | 'down'
  | 'degraded'
  | 'partial'
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
  down: 'Down',
  degraded: 'Degraded',
  partial: 'Partial outage',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
  missing: 'Missing data',
}

/**
 * The same default label text a bare `<StatusBadge status={status} />`
 * renders (STORY-100) — exported so a caller that needs the WORD (not the
 * badge markup) reuses the SAME vocabulary rather than a second copy. E.g.
 * the Approvals confirm-step consequence copy ("Publishes '<component>:
 * <target status>' …") names the target status using this, so it always
 * matches the word the transition badge itself already shows.
 */
export function defaultStatusLabel(status: HealthStatus): string {
  return DEFAULT_LABELS[status]
}

/**
 * Pill status indicator (STORY-015a AC4/AC6). Status is NEVER conveyed by
 * color alone: a decorative dot (aria-hidden) carries the health color, and
 * an ink-colored text label always accompanies it — the label is the
 * accessible name, not the dot.
 */
export function StatusBadge({ status, label }: StatusBadgeProps) {
  const text = label ?? DEFAULT_LABELS[status]

  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className="status-badge__dot" aria-hidden="true" />
      <span className="status-badge__label">{text}</span>
    </span>
  )
}
