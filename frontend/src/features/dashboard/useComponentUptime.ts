import { useCallback } from 'react'
import { getComponentAvailability, getHistory } from '../../api/client'
import type { ComponentTopologyDTO, ObservationDTO } from '../../api/types'
import type { UptimeSegment } from '../../components'
import type { AvailabilityRange } from '../availability/windowRange'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'
import { buildUptimeSegments } from '../history/uptimeSegments'
import { buildLatencyPoints } from './latencyPoints'

export interface ComponentUptime {
  /** The rollup `availability_pct` (a 0-1 fraction, or `null` on a
   * degenerate/no-data window) — ALSO `null` when the fetch itself failed,
   * so a transport error renders identically to a genuine no-data window
   * (never a fabricated number). */
  pct: number | null
  /** Oldest -> newest, capped at `MAX_UPTIME_SEGMENTS`. EMPTY (never
   * fabricated) when the component has no signals, its signal has no
   * observations in the window, or the fetch failed — handed straight to
   * `UptimeBar`, whose own empty-segments branch renders the explicit
   * "No data" state instead of a zero-segment bar. */
  segments: UptimeSegment[]
  /** Oldest -> newest non-null latency values, capped at
   * `MAX_LATENCY_POINTS` (STORY-105, additive — the Dashboard tile's inline
   * latency spark). Derived from the SAME `observations` fetch `segments`
   * already uses — no extra network call. EMPTY under the same conditions
   * `segments` is empty (never fabricated). */
  latencyPoints: number[]
  /** ISO timestamp of the primary signal's most recent observation in the
   * window (STORY-105, additive — the Dashboard tile's "Last observed"
   * `RelativeTime`), or `null` when there is none (no signals, no
   * observations, or the fetch failed). `observations` arrives newest-first,
   * so this is simply its first entry. */
  lastObservedIso: string | null
}

/**
 * Per-component uptime fetch (STORY-057 AC3) — combines the rollup
 * `availability_pct` (`getComponentAvailability`) with a sparkline built
 * from the component's FIRST topology signal's raw history (`getHistory`).
 * Adapts to what these two EXISTING endpoints provide; there is no
 * dedicated per-component uptime-bucket API yet (deferred to STORY-067).
 * A component with zero signals skips the history call entirely (`segments`
 * stays empty — never fabricated).
 *
 * NEVER throws: any failure for THIS component (network, 404, malformed
 * body) degrades to `{ pct: null, segments: [] }` rather than rejecting —
 * so `fetchAllComponentUptime`'s `Promise.all` below can never have one
 * troubled component blank every other row's real data.
 */
async function fetchComponentUptime(
  component: ComponentTopologyDTO,
  range: AvailabilityRange,
): Promise<ComponentUptime> {
  try {
    const primarySignal = component.signals[0]
    const [availability, observations] = await Promise.all([
      getComponentAvailability(component.id, range),
      primarySignal
        ? getHistory({
            signal_key: primarySignal.signal_key,
            since: range.since,
            until: range.until,
          })
        : Promise.resolve<ObservationDTO[]>([]),
    ])

    return {
      pct: availability.rollup.availability_pct,
      segments: buildUptimeSegments(observations),
      latencyPoints: buildLatencyPoints(observations),
      lastObservedIso: observations[0]?.observed_at ?? null,
    }
  } catch {
    return { pct: null, segments: [], latencyPoints: [], lastObservedIso: null }
  }
}

async function fetchAllComponentUptime(
  topology: ComponentTopologyDTO[],
  range: AvailabilityRange,
): Promise<Record<string, ComponentUptime>> {
  const results = await Promise.all(
    topology.map((component) => fetchComponentUptime(component, range)),
  )

  const byComponentId: Record<string, ComponentUptime> = {}
  topology.forEach((component, index) => {
    byComponentId[component.id] = results[index]
  })
  return byComponentId
}

export type UseComponentUptimeResult = UseFetchResult<Record<string, ComponentUptime>>

/**
 * Read hook for the Dashboard's per-row uptime %/sparkline (STORY-057 AC3).
 * `fetchComponentUptime` never rejects, so in practice this hook's OWN
 * state reaches `'success'` as soon as `topology`/`range` settle — real
 * per-component failures resolve to a no-data entry instead of an error
 * state. `DashboardPage` treats this hook exactly like the EXISTING
 * `useMaintenanceWindows` overlay pattern: any non-`'success'` phase
 * (including the brief initial loading tick, or the unexpected case this
 * DOES land in `'error'`) means "no uptime data yet for any row" — an
 * enhancement, never a reason to block the primary components table (AC2's
 * graceful-degradation spirit, extended to this hook).
 */
export function useComponentUptime(
  topology: ComponentTopologyDTO[],
  range: AvailabilityRange,
): UseComponentUptimeResult {
  const fetcher = useCallback(
    () => fetchAllComponentUptime(topology, range),
    [topology, range],
  )
  return useFetch(fetcher)
}
