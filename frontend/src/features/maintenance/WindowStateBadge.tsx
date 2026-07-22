import { cx } from '../../lib/cx'
import type { MaintenanceWindowState } from './deriveWindowState'
import './WindowStateBadge.css'

export interface WindowStateBadgeProps {
  state: MaintenanceWindowState
}

const LABELS: Record<MaintenanceWindowState, string> = {
  upcoming: 'Upcoming',
  active: 'Active',
  past: 'Past',
}

/**
 * The client-derived upcoming/active/past pill (STORY-132 AC1) — dot + text
 * label, never colour alone (same shape as `StatusBadge`, but a distinct,
 * smaller vocabulary that is NOT a health status, so it gets its own type
 * rather than overloading `StatusBadge`'s `HealthStatus` union with values
 * that aren't health at all).
 */
export function WindowStateBadge({ state }: WindowStateBadgeProps) {
  return (
    <span className={cx('window-state-badge', `window-state-badge--${state}`)}>
      <span className="window-state-badge__dot" aria-hidden="true" />
      <span className="window-state-badge__label">{LABELS[state]}</span>
    </span>
  )
}
