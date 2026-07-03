/**
 * Formats an availability/completeness percentage for display (STORY-015d
 * AC1, AC3). The backend (`core/services/availability.py`) puts these on
 * the wire as 0-1 FRACTIONS (e.g. `1.0` for 100% up, `0.9987` for 99.87%),
 * never pre-multiplied — this is the one seam that scales fraction -> the
 * two-decimal-place percent string display expects (e.g. `99.87%`). `null`
 * (a degenerate window — no verdicts, or a component/signal with no data
 * yet) renders as the explicit "no data" label — NEVER `0%` (which would
 * misreport a real outage as "no data") and never `NaN%`.
 */
export function formatPct(pct: number | null): string {
  return pct === null ? 'no data' : `${(pct * 100).toFixed(2)}%`
}
