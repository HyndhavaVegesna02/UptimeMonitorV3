import type { ObservationDTO } from '../../api/types'
import type { UptimeSegment } from '../../components'
import { observationHealth } from '../history/observationHealth'

/** The most segments the Availability grid's sparkline ever renders
 * (STORY-058 AC1) — mirrors the Dashboard's own cap
 * (`features/dashboard/useComponentUptime.ts::MAX_UPTIME_SEGMENTS`), kept as
 * this feature's own copy per the sprint-38 Wave-2 file-scope isolation
 * rule (each redesigned tab owns its presentation constants). */
export const MAX_AVAILABILITY_SEGMENTS = 30

/**
 * Builds `UptimeBar` segments from ONE signal's raw observations
 * (STORY-058 AC1) — real per-check history, never a fabricated bucket.
 * `getHistory` returns newest-first; this takes the most recent
 * `MAX_AVAILABILITY_SEGMENTS` and reverses them so the bar reads oldest
 * (left) -> newest (right), matching the reference mock's left-to-right
 * timeline (mirrors `features/dashboard/useComponentUptime.ts
 * ::buildUptimeSegments`, kept as a separate copy — see module doc).
 */
export function buildAvailabilitySegments(observations: ObservationDTO[]): UptimeSegment[] {
  return observations
    .slice(0, MAX_AVAILABILITY_SEGMENTS)
    .slice()
    .reverse()
    .map((observation) => ({
      status: observationHealth(observation.health),
      title: `${observation.location} — ${observation.health} @ ${observation.observed_at}`,
    }))
}
