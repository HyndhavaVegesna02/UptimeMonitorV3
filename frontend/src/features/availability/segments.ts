import type { ObservationDTO } from '../../api/types'
import type { UptimeSegment } from '../../components'
import { buildUptimeSegments, MAX_UPTIME_SEGMENTS } from '../history/uptimeSegments'

/** The most segments the Availability grid's sparkline ever renders
 * (STORY-058 AC1) — mirrors the Dashboard's own cap
 * (`features/history/uptimeSegments.ts::MAX_UPTIME_SEGMENTS`). */
export const MAX_AVAILABILITY_SEGMENTS = MAX_UPTIME_SEGMENTS

/**
 * Builds `UptimeBar` segments from ONE signal's raw observations
 * (STORY-058 AC1) — real per-check history, never a fabricated bucket.
 * Delegates to the shared buildUptimeSegments helper.
 */
export function buildAvailabilitySegments(observations: ObservationDTO[]): UptimeSegment[] {
  return buildUptimeSegments(observations)
}
