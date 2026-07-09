import type { HealthStatus } from '../StatusBadge/StatusBadge'
import { cx } from '../../lib/cx'
import './UptimeBar.css'

export interface UptimeSegment {
  /** Which health color paints this segment. */
  status: HealthStatus
  /** Tooltip text shown on hover/focus for this individual segment (e.g. a
   * per-period summary — "Jul 03 — degraded"). */
  title: string
}

export interface UptimeBarProps {
  segments: UptimeSegment[]
  /** Accessible label for the bar as a whole (STORY-055 AC5). */
  label?: string
  className?: string
}

/**
 * N-segment uptime sparkline (STORY-055 AC5) — used by Dashboard (per-
 * component 30-segment strip) and Availability (per-window strip). Each
 * segment is colored by its `HealthStatus` via a token-driven modifier
 * class (never inline hex) and carries its own `title` tooltip. Renders an
 * explicit "No data" state instead of a zero-segment bar when `segments` is
 * empty — the caller must never fabricate segments to avoid this state.
 */
export function UptimeBar({ segments, label = 'Uptime segments', className }: UptimeBarProps) {
  if (segments.length === 0) {
    return (
      <div
        className={cx('uptime-bar', 'uptime-bar--empty', className)}
        role="img"
        aria-label={`${label}: no data`}
      >
        <span className="uptime-bar__no-data">No data</span>
      </div>
    )
  }

  const order: HealthStatus[] = ['up', 'down', 'degraded', 'partial', 'maintenance', 'unknown', 'missing']
  const summary = order
    .map((status) => {
      const count = segments.filter((s) => s.status === status).length
      return count > 0 ? `${count} ${status}` : null
    })
    .filter(Boolean)
    .join(', ')

  const fullLabel = summary ? `${label} (${summary})` : label

  return (
    <div className={cx('uptime-bar', className)} role="img" aria-label={fullLabel}>
      {segments.map((segment, index) => (
        <span
          key={index}
          className={cx('uptime-bar__segment', `uptime-bar__segment--${segment.status}`)}
          title={segment.title}
        />
      ))}
    </div>
  )
}
