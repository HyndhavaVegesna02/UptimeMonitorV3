import type { ObservationDTO } from '../../api/types'
import type { UptimeSegment } from '../../components'
import { observationHealth } from './observationHealth'

/** The most segments a sparkline ever renders (STORY-069) — mirrors the
 * sprint-38 mock's ~30-segment strip. */
export const MAX_UPTIME_SEGMENTS = 30

/**
 * Builds sparkline segments from ONE signal's raw observations (STORY-069)
 * — real per-check history, never a fabricated bucket. `getHistory`
 * returns newest-first; this takes the most recent `MAX_UPTIME_SEGMENTS`
 * and reverses them so the bar reads oldest (left) -> newest (right),
 * matching the reference mock's left-to-right timeline.
 */
export function buildUptimeSegments(observations: ObservationDTO[]): UptimeSegment[] {
  return observations
    .slice(0, MAX_UPTIME_SEGMENTS)
    .slice()
    .reverse()
    .map((observation) => ({
      status: observationHealth(observation.health),
      title: `${observation.location} — ${observation.health} @ ${observation.observed_at}`,
    }))
}
