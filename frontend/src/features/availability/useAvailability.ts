import { useCallback } from 'react'
import { getComponentAvailability, getTopology } from '../../api/client'
import type { ComponentAvailabilityDTO, ComponentTopologyDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'
import type { AvailabilityRange } from './windowRange'

/** The merged two-grain payload the Availability tab renders (STORY-015d
 * AC1): every component (topology) plus its own availability result,
 * keyed by `component_id` for O(1) lookup while rendering each row. */
export interface AvailabilityBundle {
  topology: ComponentTopologyDTO[]
  availabilityByComponent: Record<string, ComponentAvailabilityDTO>
}

export type UseAvailabilityResult = UseFetchResult<AvailabilityBundle>

/**
 * Fetches the full two-grain availability bundle for a window (STORY-015d
 * AC1, AC2): `getTopology()` first, then a `Promise.all` of
 * `getComponentAvailability(component.id, range)` per component, merged
 * into `{ topology, availabilityByComponent }`. If any single component's
 * availability call rejects, the whole `Promise.all` rejects — an accepted
 * whole-tab error (not a per-row partial failure) per the sprint-32 plan.
 */
export async function fetchAvailabilityBundle(
  range: AvailabilityRange,
): Promise<AvailabilityBundle> {
  const topology = await getTopology()
  const results = await Promise.all(
    topology.map((component) => getComponentAvailability(component.id, range)),
  )

  const availabilityByComponent: Record<string, ComponentAvailabilityDTO> = {}
  topology.forEach((component, index) => {
    availabilityByComponent[component.id] = results[index]
  })

  return { topology, availabilityByComponent }
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
