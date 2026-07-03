/**
 * Formats an availability/completeness percentage for display (STORY-015d
 * AC1, AC3): two decimal places, consistent precision (e.g. `99.87%`).
 * `null` (a degenerate window — no verdicts, or a component/signal with no
 * data yet) renders as the explicit "no data" label — NEVER `0%` (which
 * would misreport a real outage as "no data") and never `NaN%`.
 */
export function formatPct(pct: number | null): string {
  return pct === null ? 'no data' : `${pct.toFixed(2)}%`
}
