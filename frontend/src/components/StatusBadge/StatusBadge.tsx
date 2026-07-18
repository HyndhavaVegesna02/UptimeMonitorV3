import './StatusBadge.css'
import { DEFAULT_LABELS } from './labels'

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
