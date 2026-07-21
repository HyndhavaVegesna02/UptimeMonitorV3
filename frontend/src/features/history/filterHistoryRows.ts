import type { HistoryRow } from './mergeHistoryRows'

export type ResultFilterKey = 'all' | 'up' | 'degraded' | 'down'

export interface ResultFilterOption {
  key: ResultFilterKey
  label: string
}

/** The Result filter's FIXED wire vocabulary (STORY-130 AC2) — pinned
 * constants, deliberately NOT derived from the loaded rows (unlike the
 * Location filter below): a window with zero "down" observations should
 * still offer "Down" as an option. */
export const RESULT_FILTER_OPTIONS: ResultFilterOption[] = [
  { key: 'all', label: 'All' },
  { key: 'up', label: 'Up' },
  { key: 'degraded', label: 'Degraded' },
  { key: 'down', label: 'Down' },
]

export interface HistoryFilters {
  search: string
  result: ResultFilterKey
  /** `'all'` or an exact `HistoryRow.location` value. */
  location: string
}

/**
 * Distinct locations found in the currently-loaded rows, sorted
 * alphabetically (STORY-130 AC2 — "Location filter whose options are
 * derived from the loaded rows", unlike the Result filter's fixed
 * vocabulary). Zero rows -> an empty array, never a crash.
 */
export function deriveLocationOptions(rows: HistoryRow[]): string[] {
  return Array.from(new Set(rows.map((row) => row.location))).sort()
}

/**
 * Applies all three client-side filters (STORY-130 AC2) — Result (fixed
 * vocabulary, exact match on the raw wire `health`), Location (exact match),
 * and a case-insensitive text search over component name / location /
 * signal_key. All three combine with AND. An empty `search` matches
 * everything (never filters out on an empty string).
 */
export function filterHistoryRows(rows: HistoryRow[], filters: HistoryFilters): HistoryRow[] {
  const search = filters.search.trim().toLowerCase()

  return rows.filter((row) => {
    if (filters.result !== 'all' && row.health !== filters.result) {
      return false
    }
    if (filters.location !== 'all' && row.location !== filters.location) {
      return false
    }
    if (search === '') {
      return true
    }
    return (
      row.componentName.toLowerCase().includes(search) ||
      row.location.toLowerCase().includes(search) ||
      row.signalKey.toLowerCase().includes(search)
    )
  })
}
