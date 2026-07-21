import { Globe } from '@phosphor-icons/react'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { Icon } from '../../components/Icon/Icon'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { formatLatency } from '../../lib/format'
import type { RecentCheckRow } from './deriveRecentChecks'
import './RecentChecksFeed.css'

export interface RecentChecksFeedProps {
  rows: RecentCheckRow[]
}

/**
 * The Dashboard's recent-checks feed (STORY-122 AC5) — the latest N
 * observations across every signal, each with component, location,
 * relative time, latency, and a health tag (dot + text, never colour
 * alone).
 */
export function RecentChecksFeed({ rows }: RecentChecksFeedProps) {
  if (rows.length === 0) {
    return (
      <Panel title="Recent checks">
        <EmptyState message="No recent checks" detail="Check activity will appear here." />
      </Panel>
    )
  }

  return (
    <Panel title="Recent checks" className="recent-checks">
      <ul className="recent-checks__list">
        {rows.map((row) => (
          <li key={row.key} className="recent-checks__row">
            <span className="recent-checks__icon" aria-hidden="true">
              <Icon icon={Globe} aria-hidden size={16} />
            </span>
            <div className="recent-checks__main">
              <div className="recent-checks__name">{row.componentName}</div>
              <div className="recent-checks__meta">
                Location {row.locationLabel} · {row.relativeTime}
              </div>
            </div>
            <div className="recent-checks__trailing">
              <div className="recent-checks__latency">
                {formatLatency(row.latencyMs)}
                {row.latencyMs !== null ? <span className="recent-checks__unit">&nbsp;ms</span> : null}
              </div>
              <StatusBadge status={row.health} />
            </div>
          </li>
        ))}
      </ul>
    </Panel>
  )
}
