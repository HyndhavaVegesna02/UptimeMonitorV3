import { getPublications } from '../../api/client'
import type { PublicationDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState, UseFetchResult } from '../../lib/useFetch'

export type PublicationsFetchState = FetchState<PublicationDTO[]>

export type UsePublicationsResult = UseFetchResult<PublicationDTO[]>

/**
 * Fetch hook for `GET /api/v1/publications` (STORY-015g AC1). A plain read
 * tab with no params — a thin `useFetch` wrapper over the module-scoped
 * `getPublications`, matching `useComponents`/`useApprovals` (no
 * parameterized-fetch shape needed here, unlike Availability/Check History).
 */
export function usePublications(): UsePublicationsResult {
  return useFetch(getPublications)
}
