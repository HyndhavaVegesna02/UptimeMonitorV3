import { useCallback, useEffect, useState } from 'react'
import { getComponents } from '../../api/client'
import type { ComponentDTO } from '../../api/types'

export type ComponentsFetchState =
  | { phase: 'loading' }
  | { phase: 'error'; message: string }
  | { phase: 'success'; data: ComponentDTO[] }

export interface UseComponentsResult {
  state: ComponentsFetchState
  retry: () => void
}

/**
 * Fetch hook for `GET /api/v1/components` (STORY-015b AC4) — extracted
 * verbatim from the STORY-015a proving example (`ComponentsProbe`) so the
 * Dashboard tab and every later tab share one fetch pattern: a
 * discriminated-union `ComponentsFetchState`, a cancelled-guarded effect
 * (never sets state after the request is stale/unmounted), and an
 * `attempt`-keyed `retry` that re-triggers the effect via a dependency bump
 * rather than calling the fetch directly from the event handler.
 */
export function useComponents(): UseComponentsResult {
  const [state, setState] = useState<ComponentsFetchState>({ phase: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    getComponents()
      .then((data) => {
        if (!cancelled) {
          setState({ phase: 'success', data })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setState({
            phase: 'error',
            message: err instanceof Error ? err.message : 'Unknown error',
          })
        }
      })

    return () => {
      cancelled = true
    }
  }, [attempt])

  const retry = useCallback(() => {
    // Reset to loading in the event handler, not synchronously inside the
    // effect body (react-hooks/set-state-in-effect) — this is what shows
    // the spinner again for the in-flight retry.
    setState({ phase: 'loading' })
    setAttempt((n) => n + 1)
  }, [])

  return { state, retry }
}
