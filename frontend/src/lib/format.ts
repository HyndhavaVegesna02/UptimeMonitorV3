/**
 * Shared numeric-formatting helpers (STORY-122) — every KPI/roster/feed
 * value that can be a degenerate `null` (a no-data availability window, a
 * missing observation latency) renders an em dash rather than a fabricated
 * `0`/`0.00` (web-interface-guidelines: never invent a number).
 */

/** Formats a 0-1 fraction (e.g. `AvailabilityDTO.availability_pct`) as a
 * percentage string, e.g. `0.9987` -> `"99.87"` (2 decimals by default). */
export function formatPercent(fraction: number | null, decimals = 2): string {
  if (fraction === null) {
    return '—'
  }
  return (fraction * 100).toFixed(decimals)
}

/** Formats a millisecond latency with thousands separators, e.g.
 * `1240` -> `"1,240"`. */
export function formatLatency(ms: number | null): string {
  if (ms === null) {
    return '—'
  }
  return ms.toLocaleString('en-US')
}
