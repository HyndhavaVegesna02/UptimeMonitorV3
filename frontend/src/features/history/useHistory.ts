import { useCallback } from 'react'
import { getHistory } from '../../api/client'
import type { ObservationDTO } from '../../api/types'
import type { AvailabilityRange } from '../availability/windowRange'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'

/** The two independently-selectable inputs the Check History fetch depends
 * on (STORY-015e AC1, AC2): which signal, and which window. */
export interface HistoryQuery {
  signalKey: string
  range: AvailabilityRange
}

export type UseHistoryResult = UseFetchResult<ObservationDTO[]>

/**
 * Read hook for the Check History tab (STORY-015e AC1, AC2), built on the
 * shared `useFetch<T>` via the STORY-015d parameterized-fetch pattern
 * (`features/availability/useAvailability.ts`'s doc comment has the full
 * rationale): the fetch depends on BOTH which signal is selected and which
 * window is selected, so the fetcher is wrapped in `useCallback` keyed on
 * `[signalKey, range]` — a NEW identity, and so exactly one refetch, when
 * EITHER axis changes, and a STABLE identity otherwise. The caller
 * (`CheckHistoryPage`) is responsible for `useMemo`-ing `range` (via
 * `features/availability/windowRange.ts::windowToRange`, REUSED rather than
 * duplicated — the parallel-shape agreement) so `range`'s own identity is
 * stable while the window preset is unchanged.
 */
export function useHistory({ signalKey, range }: HistoryQuery): UseHistoryResult {
  const fetcher = useCallback(
    () => getHistory({ signal_key: signalKey, since: range.since, until: range.until }),
    [signalKey, range],
  )
  return useFetch(fetcher)
}
