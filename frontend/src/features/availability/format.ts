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

/** The subset of `AvailabilityDTO` the availability grid's "down" label
 * needs (STORY-058 AC1) — kept structural (not the full DTO) so this stays
 * usable from both a rollup and a per-signal `SignalAvailabilityDTO`. */
export interface DownCounts {
  availability_pct: number | null
  total_verdicts: number
  passing_verdicts: number
  maintenance_verdicts: number
}

/**
 * The Availability cell's "down" sublabel (STORY-058 AC1) — derived from the
 * REAL verdict counts on the wire (`total − passing − maintenance`), never a
 * fabricated count. Mirrors the reference mock's phrasing
 * (`docs/scrum/sprints/2026-07-07-sprint-38/reference-operator-dashboard.dc.html`
 * line 718: `st.down ? (st.down + (st.down===1?' period down':' periods
 * down')) : 'no downtime'`). A `null` `availability_pct` (a degenerate
 * window — the availability denominator is zero) has no verdicts to count,
 * so it renders "no data" — matching `formatPct`'s own null case rather than
 * the misleading `0 periods down`/`no downtime`.
 */
export function formatDownLabel(rollup: DownCounts): string {
  if (rollup.availability_pct === null) {
    return 'no data'
  }
  const down = rollup.total_verdicts - rollup.passing_verdicts - rollup.maintenance_verdicts
  if (down <= 0) {
    return 'no downtime'
  }
  return `${down} period${down === 1 ? '' : 's'} down`
}

/** The completeness threshold below which the grid flags "missing data"
 * (STORY-058 AC1) — mirrors the reference mock's `complPct<98` band
 * (line 720), expressed here as a 0-1 fraction to match the wire scale. */
export const COMPLETENESS_LOW_THRESHOLD = 0.98

/**
 * True when `pct` is a REAL, measured completeness below the "missing data"
 * threshold (STORY-058 AC1). A `null` pct (no data at all — a zero
 * denominator) is deliberately NOT "low": that is a distinct "no data"
 * condition already surfaced by `formatPct`'s own "no data" text, not a
 * partial-completeness warning.
 */
export function isCompletenessLow(pct: number | null): boolean {
  return pct !== null && pct < COMPLETENESS_LOW_THRESHOLD
}

/** The four health bands the availability grid colors its headline % by
 * (STORY-058 AC1) — mirrors the reference mock's `thColor` bands (line 589:
 * `p>=99.9?ok:p>=99?degraded:p>=95?partial:major`), expressed as 0-1
 * fractions and named after this app's `HealthStatus` tokens. */
export type AvailabilityBand = 'up' | 'degraded' | 'partial' | 'down'

/**
 * Bands a REAL `availability_pct` fraction into one of the four health
 * colors (STORY-058 AC1) — `null` (no data) bands to `null` so the caller
 * renders the default ink color rather than fabricating a health verdict for
 * a window with nothing to judge.
 */
export function availabilityBand(pct: number | null): AvailabilityBand | null {
  if (pct === null) {
    return null
  }
  if (pct >= 0.999) {
    return 'up'
  }
  if (pct >= 0.99) {
    return 'degraded'
  }
  if (pct >= 0.95) {
    return 'partial'
  }
  return 'down'
}
