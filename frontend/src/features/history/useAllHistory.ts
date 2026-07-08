import { useCallback } from 'react'
import { getHistory, getTopology } from '../../api/client'
import type { AvailabilityRange } from '../availability/windowRange'
import { useFetch } from '../../lib/useFetch'
import type { UseFetchResult } from '../../lib/useFetch'
import { flattenSignals } from './signals'
import { mergeObservations } from './mergeObservations'
import type { HistoryRow } from './mergeObservations'

export type UseAllHistoryResult = UseFetchResult<HistoryRow[]>

/**
 * Read hook for the STORY-060 Check History tab: a system-wide, newest-first
 * observation ledger rather than one signal at a time (the pre-STORY-060
 * shape `useHistory`/`useSignalOptions` implemented — superseded by this
 * hook and removed).
 *
 * There is no "history for every signal" endpoint (`GET /api/v1/history`
 * always takes exactly one `signal_key` — the STORY-060 plan's pinned
 * contract), so this enumerates the signals via the EXISTING
 * `GET /api/v1/topology` (reused, not re-added) and fires one `getHistory`
 * call per signal IN PARALLEL for the given window, then merges the results
 * via `mergeObservations`. The whole thing is wrapped as a SINGLE `useFetch`
 * fetcher so the page gets one loading/error/success state to render instead
 * of juggling a topology phase and a history phase separately.
 *
 * `range` must be a stable reference across renders while the window preset
 * is unchanged (the caller memoizes it via `windowToRange`, same discipline
 * as `useAvailability`/the old `useHistory`) — it is the sole dependency
 * that changes this fetcher's identity.
 */
export function useAllHistory(range: AvailabilityRange): UseAllHistoryResult {
  const fetcher = useCallback(async () => {
    const topology = await getTopology()
    const signals = flattenSignals(topology)

    const entries = await Promise.all(
      signals.map(async (signal) => {
        const observations = await getHistory({
          signal_key: signal.signal_key,
          since: range.since,
          until: range.until,
        })
        return [signal.signal_key, observations] as const
      }),
    )

    const observationsBySignal = Object.fromEntries(entries)
    return mergeObservations(signals, observationsBySignal)
  }, [range])

  return useFetch(fetcher)
}
