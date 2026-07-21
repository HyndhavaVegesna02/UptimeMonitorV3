import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import type { AvailabilityDTO } from '../../api/types'

/**
 * Formats a 0-1 fraction (`AvailabilityDTO.availability_pct`/
 * `completeness_pct`) as a display percentage's NUMERIC part, e.g.
 * `0.0930555` -> `"9.31"` (STORY-129 AC4). `null` (a degenerate/no-data
 * window) renders "No data" - NEVER a fabricated `0%`; a genuine `0`
 * fraction (an actual all-failing window) is distinct and DOES render
 * `"0.00"`. Deliberately returns the number WITHOUT a `%` suffix - same
 * convention as `lib/format.ts::formatLatency`: the caller renders the unit
 * as a sibling JSX text node with a literal `&nbsp;` entity (e.g.
 * `ComponentsRoster.tsx`), never embedded in the returned string.
 */
export function formatAvailabilityPercent(fraction: number | null): string {
  if (fraction === null) {
    return 'No data'
  }
  return (fraction * 100).toFixed(2)
}

/** Below this completeness fraction, the page flags the row as low-data
 * (STORY-129 AC4/plan §Availability capabilities: "a low-completeness
 * indicator"). Chosen so a genuinely degenerate real-world window (the live
 * sample's 9.3% completeness) IS flagged - this is a common, expected signal
 * in this system's synthetic-monitor gap pattern, not a rare edge case. */
export const LOW_COMPLETENESS_THRESHOLD = 0.5

/** `null` is explicitly NOT "low completeness" (AC4) - it is "no data",
 * a distinct, more severe case the caller renders separately. */
export function isLowCompleteness(completenessPct: number | null): boolean {
  return completenessPct !== null && completenessPct < LOW_COMPLETENESS_THRESHOLD
}

/** Below this availability fraction, `availabilityBand` reports "down"
 * rather than "up" (plan §Availability: "a band, e.g. >=99.9 healthy ...
 * else down"). */
const HEALTHY_AVAILABILITY_THRESHOLD = 0.999

/**
 * Bands an availability fraction into a health status for `StatusBadge`
 * (STORY-129 AC4). `null` bands as `"missing"` - the 7-status vocabulary's
 * dedicated "no data" status - distinct from `"down"`, which means data
 * exists and it is bad.
 */
export function availabilityBand(availabilityPct: number | null): HealthStatus {
  if (availabilityPct === null) {
    return 'missing'
  }
  return availabilityPct >= HEALTHY_AVAILABILITY_THRESHOLD ? 'up' : 'down'
}

/**
 * Derives the "down" verdict count the wire doesn't carry directly (plan
 * §Availability capabilities: "down = total - passing - maintenance") -
 * `gap_verdicts` is a SEPARATE real field (missing-data intervals), not
 * folded into this derived figure.
 */
export function deriveDownCount(availability: AvailabilityDTO): number {
  return availability.total_verdicts - availability.passing_verdicts - availability.maintenance_verdicts
}
