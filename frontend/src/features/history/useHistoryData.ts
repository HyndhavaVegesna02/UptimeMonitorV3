import { useEffect, useMemo, useState } from 'react'
import { getHistoryWindow } from '../../api/client'
import type { ComponentTopologyDTO, ObservationDTO } from '../../api/types'
import type { FetchState } from '../../lib/useFetch'

export type ObservationsBySignal = Record<string, ObservationDTO[]>

/** The per-signal server-side cap (STORY-130) — deliberately larger than
 * the client render cap (`capRows.ts`'s default 1000): the server-side
 * `limit` bounds bytes-over-the-wire per signal, the client cap bounds
 * DOM rows across ALL merged signals; the two are independent concerns. */
const FETCH_LIMIT = 1000

interface Resolved {
  /** The request identity (`signalKeysKey|since|until`) this resolved state
   * corresponds to — lets the render-time phase computation below tell
   * "stale result, a fetch for the CURRENT request is in flight" apart from
   * "this IS the current result", without a synchronous `setState` inside
   * the effect body (same discipline as `dashboard/useSignalsData.ts`). */
  key: string
  state: FetchState<ObservationsBySignal>
}

/**
 * Fetches windowed history for every signal in the topology (STORY-130
 * AC1) — genuinely sequenced after `topologyState` (there is no signal_key
 * to query before topology resolves, same reasoning as
 * `dashboard/useSignalsData.ts`), but every signal's own fetch then runs in
 * parallel (`Promise.all`), never one at a time. Re-fetches whenever
 * `since`/`until` change — the window toggle is the only control that
 * should trigger a refetch (plan §History capabilities).
 */
export function useHistoryData(
  topologyState: FetchState<ComponentTopologyDTO[]>,
  since: string,
  until: string,
): FetchState<ObservationsBySignal> {
  const topology = topologyState.phase === 'success' ? topologyState.data : null
  const signalKeys = useMemo(
    () => (topology ?? []).flatMap((component) => component.signals.map((signal) => signal.signal_key)),
    [topology],
  )
  const signalKeysKey = signalKeys.join(',')
  const requestKey = `${signalKeysKey}|${since}|${until}`

  const [resolved, setResolved] = useState<Resolved>({ key: '', state: { phase: 'success', data: {} } })

  useEffect(() => {
    if (topologyState.phase !== 'success' || signalKeysKey === '') {
      return
    }

    const keys = signalKeysKey.split(',')
    let cancelled = false

    Promise.all(
      keys.map(async (key) => {
        const observations = await getHistoryWindow({ signal_key: key, since, until, limit: FETCH_LIMIT })
        return [key, observations] as const
      }),
    )
      .then((entries) => {
        if (!cancelled) {
          setResolved({ key: requestKey, state: { phase: 'success', data: Object.fromEntries(entries) } })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setResolved({
            key: requestKey,
            state: { phase: 'error', message: err instanceof Error ? err.message : 'Unknown error' },
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [topologyState.phase, signalKeysKey, since, until, requestKey])

  if (topologyState.phase === 'loading') {
    return { phase: 'loading' }
  }
  if (topologyState.phase === 'error') {
    return { phase: 'error', message: topologyState.message }
  }
  if (signalKeysKey === '') {
    return { phase: 'success', data: {} }
  }
  if (resolved.key !== requestKey) {
    return { phase: 'loading' }
  }
  return resolved.state
}
