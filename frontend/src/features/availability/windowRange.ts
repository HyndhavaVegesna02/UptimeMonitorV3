export type WindowKey = '24h' | '7d' | '30d'

export interface WindowOption {
  key: WindowKey
  label: string
}

/** The page's 24h/7d/30d window toggle (STORY-129 AC3), in display order. */
export const WINDOW_OPTIONS: WindowOption[] = [
  { key: '24h', label: '24h' },
  { key: '7d', label: '7d' },
  { key: '30d', label: '30d' },
]

const WINDOW_HOURS: Record<WindowKey, number> = {
  '24h': 24,
  '7d': 24 * 7,
  '30d': 24 * 30,
}

export interface WindowRange {
  since: string
  until: string
}

/**
 * Computes `since`/`until` for a selected window (STORY-129 AC3) — both
 * tz-aware UTC ISO strings with a trailing `Z` (`Date.prototype.toISOString`),
 * `until` pinned to the given `now` reference (never a fresh `new Date()`
 * read internally, so the caller controls exactly when it re-derives — see
 * `AvailabilityPage`'s stable-fetcher-reference discipline). Naive datetimes
 * are never emitted; the backend 422s one (global API contract fact).
 */
export function computeWindowRange(windowKey: WindowKey, now: Date): WindowRange {
  const until = now
  const since = new Date(until.getTime() - WINDOW_HOURS[windowKey] * 60 * 60 * 1000)
  return { since: since.toISOString(), until: until.toISOString() }
}
