/** The default client-side render cap (STORY-130 AC4 — "cap rendered rows,
 * e.g. latest 1000"). */
export const DEFAULT_RENDER_CAP = 1000

export interface CappedRows<T> {
  rows: T[]
  /** The pre-cap row count, so the caller can render "showing latest N of
   * M" without re-deriving it from the caller's own filtered list. */
  total: number
  truncated: boolean
}

/**
 * Caps an already-sorted row list at `cap` entries (STORY-130 AC4). The
 * cap is a plain parameter — never hardcoded internally — so a test can
 * inject a small cap to exercise the truncated-caption path without
 * fixturing 1000+ rows.
 */
export function capRows<T>(rows: T[], cap: number): CappedRows<T> {
  return {
    rows: rows.slice(0, cap),
    total: rows.length,
    truncated: rows.length > cap,
  }
}
