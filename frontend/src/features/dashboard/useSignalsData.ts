import { useEffect, useMemo, useState } from 'react'
import { getAvailability, getHistory } from '../../api/client'
import type { ComponentDTO } from '../../api/types'
import type { FetchState } from '../../lib/useFetch'
import type { SignalsMap } from './types'

const HISTORY_LIMIT = 100

interface Resolved {
  /** The `signalKeysKey` this resolved state corresponds to — lets the
   * render-time phase computation below tell "stale result, a fetch for
   * the CURRENT keys is in flight" apart from "this IS the current
   * result", without a synchronous `setState` inside the effect body
   * (react-hooks/set-state-in-effect — every `setState` here happens
   * inside a genuine async `.then()`/`.catch()`, same pattern as `useFetch`). */
  key: string
  state: FetchState<SignalsMap>
}

/**
 * Fetches per-signal history + availability for every component (STORY-122)
 * — in the current topology a component id IS its signal_key 1:1 (dossier
 * live sample: the "http-check" component's id equals the history/
 * availability `signal_key`), so this derives the signal keys straight
 * from the ALREADY-fetched components list rather than hardcoding
 * "http-check" (AC1/AC3's "derive, don't invent").
 *
 * Genuinely sequenced after `componentsState` (there is no signal_key to
 * query before components resolve) — not a needless waterfall. Once
 * components are known, every signal's history + availability fetch runs
 * in parallel (`Promise.all`), never one-at-a-time.
 */
export function useSignalsData(componentsState: FetchState<ComponentDTO[]>): FetchState<SignalsMap> {
  const components = componentsState.phase === 'success' ? componentsState.data : null
  const signalKeys = useMemo(() => (components ?? []).map((component) => component.id), [components])
  const signalKeysKey = signalKeys.join(',')

  const [resolved, setResolved] = useState<Resolved>({ key: '', state: { phase: 'success', data: {} } })

  useEffect(() => {
    // Zero components resolves to `{}` at render time below, with no fetch
    // and no state write at all — nothing to synchronize here.
    if (componentsState.phase !== 'success' || signalKeysKey === '') {
      return
    }

    const keys = signalKeysKey.split(',')
    let cancelled = false

    Promise.all(
      keys.map(async (key) => {
        const [history, availability] = await Promise.all([getHistory(key, HISTORY_LIMIT), getAvailability(key)])
        return [key, { history, availability }] as const
      }),
    )
      .then((entries) => {
        if (!cancelled) {
          setResolved({ key: signalKeysKey, state: { phase: 'success', data: Object.fromEntries(entries) } })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setResolved({
            key: signalKeysKey,
            state: { phase: 'error', message: err instanceof Error ? err.message : 'Unknown error' },
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [componentsState.phase, signalKeysKey])

  if (componentsState.phase === 'loading') {
    return { phase: 'loading' }
  }
  if (componentsState.phase === 'error') {
    return { phase: 'error', message: componentsState.message }
  }
  if (signalKeysKey === '') {
    return { phase: 'success', data: {} }
  }
  // A resolved result for a DIFFERENT key set means the effect above has an
  // in-flight fetch for the CURRENT keys that hasn't settled yet.
  if (resolved.key !== signalKeysKey) {
    return { phase: 'loading' }
  }
  return resolved.state
}
