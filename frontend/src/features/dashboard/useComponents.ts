import { getComponents } from '../../api/client'
import type { ComponentDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState, UseFetchResult } from '../../lib/useFetch'

export type ComponentsFetchState = FetchState<ComponentDTO[]>

export type UseComponentsResult = UseFetchResult<ComponentDTO[]>

/**
 * Fetch hook for `GET /api/v1/components` (STORY-015b AC4). Built on the
 * shared `useFetch<T>` (STORY-015c AC5) — this used to hold the fetch effect
 * itself (a discriminated-union state, a cancelled-guarded effect, an
 * `attempt`-keyed retry); that logic now lives once in `useFetch` and every
 * tab's fetch hook, including this one, is a thin wrapper over it.
 */
export function useComponents(): UseComponentsResult {
  return useFetch(getComponents)
}
