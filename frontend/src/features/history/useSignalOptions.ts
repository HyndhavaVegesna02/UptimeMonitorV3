import { getTopology } from '../../api/client'
import type { ComponentTopologyDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'

export type UseSignalOptionsResult = UseFetchResult<ComponentTopologyDTO[]>

/**
 * Thin `useFetch` wrapper over the EXISTING `getTopology()` client fn
 * (STORY-044/015d) — reused here purely to enumerate signals for the Check
 * History tab's selector (STORY-015e AC1); no new topology-fetch machinery,
 * no duplicated `useFetch` effect body (parallel-shape agreement, mirrors
 * `useComponents`/`useApprovals`). Pair with `features/history/signals.ts::
 * flattenSignals` to turn the nested topology into a flat selector list.
 */
export function useSignalOptions(): UseSignalOptionsResult {
  return useFetch(getTopology)
}
