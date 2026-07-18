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
 * The default human word for a status (STORY-107) — the SAME text this
 * badge itself renders absent a `label` override. Exported so any surface
 * naming a status in prose (e.g. the Approvals approve-confirm consequence
 * copy, `features/approvals/decisionState.ts::confirmPrompt`) reuses this
 * single source of truth rather than inventing a second vocabulary for the
 * same status.
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
