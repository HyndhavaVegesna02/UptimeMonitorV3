import { formatLocationLabel } from '../../lib/formatLocation'
import { ALL_LOCATIONS, ALL_RESULTS } from './filterHistory'
import type { HistoryFilters } from './filterHistory'
import type { HistoryRow } from './mergeObservations'

/**
 * Counts the `down`-health rows in `rows` (STORY-108 AC2, the "N checks · M
 * down" results-summary line). An empty input returns `0` — the explicit,
 * tested empty-input case, never a leaked stdlib error.
 */
export function countDownRows(rows: HistoryRow[]): number {
  return rows.filter((row) => row.health === 'down').length
}

/**
 * Describes which of the three toolbar filters are currently narrowing the
 * table (STORY-108 AC2's "active-filter echo") as an ordered list of plain-
 * English fragments — `[]` when every filter is at its default (nothing to
 * echo). A location is described via `formatLocationLabel` (the short
 * display form), never the raw vendor id.
 */
export function describeActiveFilters(filters: HistoryFilters): string[] {
  const parts: string[] = []
  const query = filters.query.trim()

  if (query.length > 0) {
    parts.push(`search "${query}"`)
  }
  if (filters.result !== ALL_RESULTS) {
    parts.push(`result: ${filters.result}`)
  }
  if (filters.location !== ALL_LOCATIONS) {
    parts.push(`location: ${formatLocationLabel(filters.location)}`)
  }

  return parts
}

/**
 * Builds the Check History table's aria-live results-summary line
 * (STORY-108 AC2): "N checks · M down" over the CURRENTLY-DISPLAYED
 * (filtered) rows, plus the active-filter echo when any filter narrows the
 * result. `rows: []` renders "0 checks · 0 down" — the explicit empty-input
 * case, never a leaked stdlib message.
 */
export function buildHistorySummary(rows: HistoryRow[], filters: HistoryFilters): string {
  const count = rows.length
  const down = countDownRows(rows)
  const base = `${count} check${count === 1 ? '' : 's'} · ${down} down`
  const activeFilters = describeActiveFilters(filters)

  return activeFilters.length > 0 ? `${base} — filtered by ${activeFilters.join(', ')}` : base
}
