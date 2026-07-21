import { EmptyState } from '../../components/EmptyState/EmptyState'
import { Panel } from '../../components/Panel/Panel'
import { Sparkline } from '../../components/Sparkline/Sparkline'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { formatLatency, formatPercent } from '../../lib/format'
import type { RosterRow } from './deriveRoster'
import './ComponentsRoster.css'

export interface ComponentsRosterProps {
  rows: RosterRow[]
}

/**
 * The Dashboard's components roster (STORY-122 AC5) — every component with
 * status (dot + label, never colour alone), 24h uptime, latest latency,
 * and a trend sparkline. "Trend" is a real latency sparkline rather than a
 * fabricated delta percentage — this story does not fetch a prior-period
 * baseline to compute one honestly.
 */
export function ComponentsRoster({ rows }: ComponentsRosterProps) {
  if (rows.length === 0) {
    return (
      <Panel title="Components">
        <EmptyState message="No components" detail="Nothing to monitor yet." />
      </Panel>
    )
  }

  return (
    <Panel title="Components" className="components-roster">
      <ul className="components-roster__list">
        {rows.map((row) => (
          <li key={row.component.id} className="components-roster__row">
            <div className="components-roster__main">
              <div className="components-roster__name">
                <StatusBadge status={row.health} />
                {row.component.name}
              </div>
              <div className="components-roster__sub">
                {formatLatency(row.latestLatencyMs)}&nbsp;ms
              </div>
            </div>
            <div className="components-roster__trend">
              {row.latencyTrend.length > 0 ? <Sparkline data={row.latencyTrend} width={64} height={22} /> : null}
            </div>
            <div className="components-roster__uptime">{formatPercent(row.uptimePct)}%</div>
          </li>
        ))}
      </ul>
    </Panel>
  )
}
