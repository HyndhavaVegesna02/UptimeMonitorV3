import type { HealthStatus } from '../components'
import './StatusDot.css'

export interface StatusDotProps {
  /** The worst-of overall status (STORY-104 AC2, `deriveOverallStatus`).
   * `undefined` while the initial components fetch is still in flight or
   * has failed — rendered as 'unknown' rather than a fabricated default. */
  status: HealthStatus | undefined
}

const LABELS: Record<HealthStatus, string> = {
  up: 'Up',
  degraded: 'Degraded',
  partial: 'Partial outage',
  down: 'Down',
  maintenance: 'Maintenance',
  unknown: 'Unknown',
  missing: 'Missing data',
}

/**
 * Live overall-status dot (STORY-104 AC2, design brief §IA), placed beside
 * the brand in the command bar: a decorative colored dot (aria-hidden)
 * paired with an sr-only text naming the state — never color alone.
 * Unlike `StatusBadge` (a table/list-cell indicator with an always-VISIBLE
 * label), this is deliberately compact for the slim top bar; the state
 * name is still in the accessibility tree, just not painted on screen.
 */
export function StatusDot({ status }: StatusDotProps) {
  const resolved = status ?? 'unknown'
  const label = LABELS[resolved]

  return (
    <span className="status-dot" title={`Overall status: ${label}`}>
      <span
        className={`status-dot__mark status-dot__mark--${resolved}`}
        aria-hidden="true"
      />
      <span className="sr-only">{`Overall status: ${label}`}</span>
    </span>
  )
}
