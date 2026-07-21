import { toHealthStatus } from '../../api/statusMapping'
import type { ComponentDTO } from '../../api/types'
import type { HealthStatus } from '../../components/StatusBadge/StatusBadge'
import { latencySeries } from './deriveKpis'
import type { SignalsMap } from './types'

export interface RosterRow {
  component: ComponentDTO
  health: HealthStatus
  /** `AvailabilityDTO.availability_pct` for this component's own signal —
   * `null` when its data hasn't loaded/there is no signal data yet (never
   * a fabricated 0). */
  uptimePct: number | null
  latestLatencyMs: number | null
  /** Latency series, oldest-first, for the roster's trend sparkline. */
  latencyTrend: number[]
}

/**
 * The Dashboard's components roster (STORY-122 AC5) — one row per real
 * component, in the API's own order. `uptimePct`/`latestLatencyMs` come
 * from that component's own fetched signal data (`signalsData[component.id]`,
 * the current topology's component-id == signal_key alignment); a
 * component with no fetched signal data yet renders honest nulls rather
 * than a crash or a fabricated figure.
 */
export function deriveRoster(components: ComponentDTO[], signalsData: SignalsMap): RosterRow[] {
  return components.map((component) => {
    const signal = signalsData[component.id]

    return {
      component,
      health: toHealthStatus(component.status),
      uptimePct: signal?.availability.availability_pct ?? null,
      latestLatencyMs: signal?.history[0]?.latency_ms ?? null,
      latencyTrend: signal ? latencySeries(signal.history) : [],
    }
  })
}
