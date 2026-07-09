import { getTopology } from '../../api/client'
import type { ComponentTopologyDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState, UseFetchResult } from '../../lib/useFetch'

export type TopologyFetchState = FetchState<ComponentTopologyDTO[]>

export type UseTopologyResult = UseFetchResult<ComponentTopologyDTO[]>

/**
 * Fetch hook for `GET /api/v1/topology` (STORY-057 AC2, AC3) — feeds the
 * Dashboard's per-component signal list: how many signals a row's expand
 * affordance will show, and which signal `useComponentUptime.ts` reads for
 * the uptime sparkline. A thin `useFetch` wrapper, mirroring
 * `useComponents.ts`'s pattern exactly. Both call the one real endpoint,
 * so there is no behavior duplicated, only the thin wrapper.
 */
export function useTopology(): UseTopologyResult {
  return useFetch(getTopology)
}
