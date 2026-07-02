import './StatusBadge.css'

export type HealthStatus = 'up' | 'down' | 'degraded' | 'maintenance' | 'unknown'

export interface StatusBadgeProps {
  status: HealthStatus
  /** Overrides the default per-status label text. */
  label?: string
}

const DEFAULT_LABELS: Record<HealthStatus, string> = {
  up: 'Up',
  down: 'Down',
  degraded: 'Degraded',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
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
