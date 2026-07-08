import type { HistoryRow } from './mergeObservations'

/** `'all'` is the sentinel for "no filter applied" on both `<select>`s
 * (STORY-060 AC1) — mirrors the reference mock's own `fr`/`fl` state shape
 * (`resultOpts`/`locOpts` both lead with an `{v:'all', ...}` entry). */
export const ALL_RESULTS = 'all'
export const ALL_LOCATIONS = 'all'

export interface HistoryFilters {
  /** Free-text query, matched case-insensitively against component name,
   * location, and signal_key (STORY-060 AC1) — never re-fetched, purely a
   * client-side narrowing of the already-loaded merged rows. */
  query: string
  /** An `ObservationDTO.health` raw value (`"up" | "down" | "degraded"`), or
   * `ALL_RESULTS`. */
  result: string
  /** A raw `location` value, or `ALL_LOCATIONS`. */
  location: string
}

export const DEFAULT_HISTORY_FILTERS: HistoryFilters = {
  query: '',
  result: ALL_RESULTS,
  location: ALL_LOCATIONS,
}

/**
 * Applies the toolbar's three filters to the merged, newest-first observation
 * list (STORY-060 AC1) — order is preserved (never re-sorted here); each
 * predicate is independent and all three AND together.
 */
export function filterHistoryRows(rows: HistoryRow[], filters: HistoryFilters): HistoryRow[] {
  const query = filters.query.trim().toLowerCase()

  return rows.filter((row) => {
    if (filters.result !== ALL_RESULTS && row.health !== filters.result) {
      return false
    }
    if (filters.location !== ALL_LOCATIONS && row.location !== filters.location) {
      return false
    }
    if (query.length > 0) {
      const haystack = `${row.componentName} ${row.location} ${row.signal_key}`.toLowerCase()
      if (!haystack.includes(query)) {
        return false
      }
    }
    return true
  })
}

/** The distinct `location` values present across `rows`, sorted
 * alphabetically — populates the location-filter `<select>` from the
 * CURRENTLY-loaded window's real data rather than an invented fixed list
 * (STORY-060 AC1; there is no dedicated locations-enumeration endpoint). */
export function uniqueLocations(rows: HistoryRow[]): string[] {
  return Array.from(new Set(rows.map((row) => row.location))).sort()
}
