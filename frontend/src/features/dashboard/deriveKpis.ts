import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentDTO, ObservationDTO } from '../../api/types'

export interface ComponentsHealthSummary {
  healthy: number
  total: number
}

/**
 * KPI 3 — "components healthy n/total" (STORY-122 AC1). Every value derived
 * from the real `GET /api/v1/components` response; an empty list is a
 * named `{ healthy: 0, total: 0 }` rather than a leaked stdlib error
 * (checklist: explicit empty-input behavior).
 */
export function summarizeComponentsHealth(components: ComponentDTO[]): ComponentsHealthSummary {
  const healthy = components.filter((component) => toHealthStatus(component.status) === 'up').length
  return { healthy, total: components.length }
}

/**
 * KPI 2 — "avg response time · 24h" (STORY-122 AC1). Averages the non-null
 * `latency_ms` values across the fetched history window, rounded to the
 * nearest millisecond. `null` for an empty/all-null window rather than a
 * fabricated `0`/`NaN`.
 */
export function averageLatencyMs(observations: ObservationDTO[]): number | null {
  const values = observations
    .map((observation) => observation.latency_ms)
    .filter((value): value is number => value !== null)

  if (values.length === 0) {
    return null
  }

  const sum = values.reduce((total, value) => total + value, 0)
  return Math.round(sum / values.length)
}

/**
 * The latency sparkline series (STORY-122 AC1) — `history` is most-recent
 * first (`ObservationDTO` ordering); a `Sparkline` wants oldest-first, so
 * this reverses before dropping nulls (a gap in latency data collapses the
 * series rather than breaking the point spacing with a fabricated value).
 */
export function latencySeries(observations: ObservationDTO[]): number[] {
  return [...observations]
    .reverse()
    .map((observation) => observation.latency_ms)
    .filter((value): value is number => value !== null)
}

/**
 * The availability sparkline series (STORY-122 AC1) — a rough per-check
 * pass/fail trend (1 = `up`, 0 = anything else) derived from the same real
 * history window, oldest-first. This is the only per-point time series the
 * API exposes for availability (the `/availability` endpoint returns one
 * aggregate figure, not a binned series), so it is the honest proxy rather
 * than an invented smooth curve.
 */
export function healthSeries(observations: ObservationDTO[]): number[] {
  return [...observations].reverse().map((observation) => (observation.health === 'up' ? 1 : 0))
}
