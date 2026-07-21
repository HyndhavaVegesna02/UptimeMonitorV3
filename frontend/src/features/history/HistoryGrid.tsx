import { StatusBadge } from '../../components/StatusBadge/StatusBadge'
import { locationLabel } from '../dashboard/locationLabel'
import { formatObservedAt } from './formatTimestamp'
import type { HistoryRow } from './mergeHistoryRows'
import { toObservationHealth } from './observationHealth'
import './HistoryGrid.css'

export interface HistoryGridProps {
  rows: HistoryRow[]
}

const COLUMN_HEADERS = ['Time', 'Check type', 'Component', 'Location', 'Result', 'Status code', 'Latency']

/** `null` -> "—" (never a fabricated `0`/`0 ms` — STORY-130 AC3/edge
 * behavior). A real `0` status code never occurs on the wire, but this
 * stays symmetric with the latency column regardless. */
function renderNullable(value: number | null): string {
  return value === null ? '—' : String(value)
}

/**
 * The dense observation grid (STORY-130 AC3) — one row per merged
 * observation. Scrolls inside its OWN `overflow-x: auto` container
 * (`.history-grid__scroll`) so the page body never scrolls horizontally
 * (plan §History edge behavior), same pattern as
 * `ComponentAvailabilityCard`'s table. Purely presentational — filtering,
 * sorting, and the render cap all happen upstream in `HistoryPage`.
 */
export function HistoryGrid({ rows }: HistoryGridProps) {
  return (
    <div className="history-grid__scroll">
      <table className="history-grid__table">
        <thead>
          <tr>
            {COLUMN_HEADERS.map((header) => (
              <th key={header} scope="col">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.key}>
              <td>{formatObservedAt(row.observedAt)}</td>
              <td>{row.checkType}</td>
              <td>{row.componentName}</td>
              <td>{locationLabel(row.location)}</td>
              <td>
                <StatusBadge status={toObservationHealth(row.health)} />
              </td>
              <td>{renderNullable(row.responseStatusCode)}</td>
              <td>
                {renderNullable(row.latencyMs)}
                {row.latencyMs !== null ? <span className="history-grid__unit">&nbsp;ms</span> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
