import { useState } from 'react'
import { EmptyState } from '../../components/EmptyState/EmptyState'
import { Panel } from '../../components/Panel/Panel'
import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { formatLatency, formatPercent } from '../../lib/format'
import type { ProbeLocationRow } from './deriveProbeLocations'
import './ProbeLocationsPanel.css'

export interface ProbeLocationsPanelProps {
  locations: ProbeLocationRow[]
}

type Metric = 'latency' | 'availability' | 'errors'

const METRICS: { id: Metric; label: string }[] = [
  { id: 'latency', label: 'Latency' },
  { id: 'availability', label: 'Availability' },
  { id: 'errors', label: 'Errors' },
]

function metricValue(row: ProbeLocationRow, metric: Metric): string {
  switch (metric) {
    case 'latency':
      return formatLatency(row.latestLatencyMs)
    case 'availability':
      return formatPercent(row.availabilityPct)
    case 'errors':
      return String(row.errorCount)
  }
}

function metricUnit(metric: Metric): string | undefined {
  switch (metric) {
    case 'latency':
      return 'ms'
    case 'availability':
      return '%'
    case 'errors':
      return undefined
  }
}

/**
 * The Dashboard's probe-locations panel (STORY-122 AC3) — one row per real
 * probe location from the fetched history (never a fabricated geo map: the
 * API carries no coordinates), each with health (dot+label, never colour
 * alone) and the selected metric. The segmented control switches which
 * metric each row's trailing value shows.
 */
export function ProbeLocationsPanel({ locations }: ProbeLocationsPanelProps) {
  const [metric, setMetric] = useState<Metric>('latency')

  if (locations.length === 0) {
    return (
      <Panel title="Probe locations">
        <EmptyState message="No probe locations" detail="No check activity in this window yet." />
      </Panel>
    )
  }

  return (
    <Panel title="Probe locations" className="probe-locations">
      <div className="probe-locations__seg-ctrl" role="group" aria-label="Metric">
        {METRICS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            aria-pressed={metric === id}
            onClick={() => setMetric(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <ul className="probe-locations__list">
        {locations.map((row) => (
          <li key={row.location} className="probe-locations__row">
            <StatusBadge status={row.health} />
            <div className="probe-locations__main">
              <div className="probe-locations__label">Location {row.label}</div>
            </div>
            <div className="probe-locations__metric">
              {metricValue(row, metric)}
              {metricUnit(metric) ? <span className="probe-locations__metric-unit">{metricUnit(metric)}</span> : null}
            </div>
          </li>
        ))}
      </ul>
    </Panel>
  )
}
