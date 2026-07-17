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

/**
 * Derives the toolbar's INITIAL filter state from the URL's search params
 * (STORY-100 AC2 — the "View checks" deep-link seam from an Approvals
 * evidence card): an optional `signal` param seeds the free-text `query`
 * field the search input already narrows by (which already matches a
 * `signal_key` substring, per `filterHistoryRows` above), so a deep link
 * lands the ledger pre-filtered to that signal. Absent, this is byte-
 * identical to `DEFAULT_HISTORY_FILTERS`. Purely an INITIAL value — the
 * caller seeds `useState` with it once; the toolbar remains fully editable
 * afterwards and is never re-synced back to the URL on further changes.
 */
export function initialHistoryFilters(searchParams: URLSearchParams): HistoryFilters {
  return {
    ...DEFAULT_HISTORY_FILTERS,
    query: searchParams.get('signal') ?? DEFAULT_HISTORY_FILTERS.query,
  }
}

/** The distinct `location` values present across `rows`, sorted
 * alphabetically — populates the location-filter `<select>` from the
 * CURRENTLY-loaded window's real data rather than an invented fixed list
 * (STORY-060 AC1; there is no dedicated locations-enumeration endpoint). */
export function uniqueLocations(rows: HistoryRow[]): string[] {
  return Array.from(new Set(rows.map((row) => row.location))).sort()
}
