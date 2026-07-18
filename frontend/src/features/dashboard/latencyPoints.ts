import type { ObservationDTO } from '../../api/types'

/** The most points a Dashboard tile's latency sparkline ever renders
 * (STORY-105, design brief §IA — the per-component tile's "latency spark").
 * Mirrors `features/history/uptimeSegments.ts::MAX_UPTIME_SEGMENTS`'s
 * cap-and-reverse shape, at a smaller volume since an inline SVG spark is a
 * denser visual than a segment strip. */
export const MAX_LATENCY_POINTS = 20

/**
 * Builds an inline-SVG-ready latency series from ONE signal's raw
 * observations (STORY-105 — the Dashboard per-component tile's latency
 * spark) — real per-check history, never a fabricated value. `getHistory`
 * returns newest-first; this drops any observation with no measurement
 * (`latency_ms: null` — never rendered as a fabricated `0`), takes the most
 * recent `MAX_LATENCY_POINTS` of what remains, and reverses them so the
 * spark reads oldest (left) -> newest (right), matching
 * `buildUptimeSegments`'s left-to-right timeline convention.
 */
export function buildLatencyPoints(observations: ObservationDTO[]): number[] {
  return observations
    .filter((observation): observation is ObservationDTO & { latency_ms: number } =>
      observation.latency_ms !== null,
    )
    .slice(0, MAX_LATENCY_POINTS)
    .reverse()
    .map((observation) => observation.latency_ms)
}
