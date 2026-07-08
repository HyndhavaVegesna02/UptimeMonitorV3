import { useCallback } from 'react'
import { getComponentAvailability, getHistory, getTopology } from '../../api/client'
import type { ComponentAvailabilityDTO, ComponentTopologyDTO } from '../../api/types'
import type { UptimeSegment } from '../../components'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'
import { buildAvailabilitySegments } from './segments'
import type { AvailabilityRange } from './windowRange'

/** The merged payload the Availability tab renders (STORY-015d AC1;
 * `segmentsByComponent` added STORY-058 AC1): every component (topology),
 * its own availability result, and its `UptimeBar` sparkline segments —
 * each keyed by `component_id` for O(1) lookup while rendering each row. */
export interface AvailabilityBundle {
  topology: ComponentTopologyDTO[]
  availabilityByComponent: Record<string, ComponentAvailabilityDTO>
  segmentsByComponent: Record<string, UptimeSegment[]>
}

export type UseAvailabilityResult = UseFetchResult<AvailabilityBundle>

/**
 * Builds ONE component's `UptimeBar` segments from its first topology
 * signal's raw history (STORY-058 AC1) — mirrors
 * `features/dashboard/useComponentUptime.ts::fetchComponentUptime`'s
 * adaptation of the same two existing endpoints; there is no dedicated
 * per-component uptime-bucket API yet (deferred to STORY-067). A component
 * with zero signals skips the history call entirely (segments stay empty —
 * never fabricated).
 *
 * NEVER throws: unlike the rollup `getComponentAvailability` call (a whole-
 * tab error is accepted for THAT), a segment sparkline is a visual
 * enhancement layered on top of the real percentages — so any failure here
 * (network, 404, malformed body) degrades to `[]` (rendered by `UptimeBar`
 * as its own explicit "No data" state) rather than blocking the entire
 * bundle.
 */
async function fetchComponentSegments(
  component: ComponentTopologyDTO,
  range: AvailabilityRange,
): Promise<UptimeSegment[]> {
  const primarySignal = component.signals[0]
  if (!primarySignal) {
    return []
  }
  try {
    const observations = await getHistory({
      signal_key: primarySignal.signal_key,
      since: range.since,
      until: range.until,
    })
    return buildAvailabilitySegments(observations)
  } catch {
    return []
  }
}

/**
 * Fetches the full availability bundle for a window (STORY-015d AC1, AC2;
 * STORY-058 AC1): `getTopology()` first, then IN PARALLEL a `Promise.all` of
 * `getComponentAvailability(component.id, range)` per component (the
 * ACCURACY-critical rollup — a rejection here fails the whole bundle, per
 * the sprint-32 plan) and a `Promise.all` of `fetchComponentSegments` (the
 * sparkline ENHANCEMENT — never rejects), merged into
 * `{ topology, availabilityByComponent, segmentsByComponent }`.
 */
export async function fetchAvailabilityBundle(
  range: AvailabilityRange,
): Promise<AvailabilityBundle> {
  const topology = await getTopology()
  const [availabilityResults, segmentResults] = await Promise.all([
    Promise.all(topology.map((component) => getComponentAvailability(component.id, range))),
    Promise.all(topology.map((component) => fetchComponentSegments(component, range))),
  ])

  const availabilityByComponent: Record<string, ComponentAvailabilityDTO> = {}
  const segmentsByComponent: Record<string, UptimeSegment[]> = {}
  topology.forEach((component, index) => {
    availabilityByComponent[component.id] = availabilityResults[index]
    segmentsByComponent[component.id] = segmentResults[index]
  })

  return { topology, availabilityByComponent, segmentsByComponent }
}

/**
 * Read hook for the Availability tab (STORY-015d AC1, AC2), built on the
 * shared `useFetch<T>`. Unlike `useComponents`/`useApprovals` (thin
 * wrappers over a parameterless module-scoped fetcher), this hook's fetcher
 * depends on `range` — so it is wrapped in `useCallback` keyed on the
 * `range` object itself. This keeps `useFetch`'s "stable fetcher reference"
 * contract intact (the identity is stable as long as the caller passes the
 * SAME range instance — which `AvailabilityPage` guarantees by memoizing
 * `windowToRange(preset)` with `useMemo` keyed on `preset`) while giving
 * the fetcher a NEW identity exactly when the window selector changes the
 * range. `useFetch`'s effect already depends on `fetcher`
 * (`frontend/src/lib/useFetch.ts`), so that identity change is what
 * re-triggers the fetch — no change to `useFetch` itself was needed (see
 * the sprint-32 plan's T3 design-decision note).
 */
export function useAvailability(range: AvailabilityRange): UseAvailabilityResult {
  const fetcher = useCallback(() => fetchAvailabilityBundle(range), [range])
  return useFetch(fetcher)
}
