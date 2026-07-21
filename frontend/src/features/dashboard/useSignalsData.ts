import { useEffect, useMemo, useState } from 'react'
import { getAvailability, getHistory } from '../../api/client'
import type { ComponentDTO } from '../../api/types'
import type { FetchState } from '../../lib/useFetch'
import type { SignalsMap } from './types'

const HISTORY_LIMIT = 100

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

  const [state, setState] = useState<FetchState<SignalsMap>>({ phase: 'loading' })

  useEffect(() => {
    if (componentsState.phase === 'loading') {
      setState({ phase: 'loading' })
      return
    }

    if (componentsState.phase === 'error') {
      setState({ phase: 'error', message: componentsState.message })
      return
    }

    const keys = signalKeysKey === '' ? [] : signalKeysKey.split(',')

    if (keys.length === 0) {
      setState({ phase: 'success', data: {} })
      return
    }

    let cancelled = false
    setState({ phase: 'loading' })

    Promise.all(
      keys.map(async (key) => {
        const [history, availability] = await Promise.all([getHistory(key, HISTORY_LIMIT), getAvailability(key)])
        return [key, { history, availability }] as const
      }),
    )
      .then((entries) => {
        if (!cancelled) {
          setState({ phase: 'success', data: Object.fromEntries(entries) })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({ phase: 'error', message: err instanceof Error ? err.message : 'Unknown error' })
        }
      })

    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [componentsState.phase, signalKeysKey])

  return state
}
