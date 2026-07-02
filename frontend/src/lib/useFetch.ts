import { useCallback, useEffect, useState } from 'react'

export type FetchState<T> =
  | { phase: 'loading' }
  | { phase: 'error'; message: string }
  | { phase: 'success'; data: T }

export interface UseFetchResult<T> {
  state: FetchState<T>
  retry: () => void
}

/**
 * Generic fetch hook (STORY-015c AC5), extracted verbatim from 015b's
 * `useComponents` so every tab's data-loading fetch hook
 * (`useComponents`, `useApprovals`, and future tabs) shares one
 * implementation instead of copy-pasting the effect body: a
 * discriminated-union `FetchState<T>`, a cancelled-guarded effect (never
 * sets state after the request is stale/unmounted), and an `attempt`-keyed
 * `retry` that re-triggers the effect via a dependency bump rather than
 * calling the fetcher directly from the event handler.
 *
 * `fetcher` must be a stable reference (a module-level function such as
 * `getComponents`/`getApprovals`, not a fresh inline closure per render) —
 * it is a `useEffect` dependency, so a fetcher that changes identity every
 * render would refetch every render.
 */
export function useFetch<T>(fetcher: () => Promise<T>): UseFetchResult<T> {
  const [state, setState] = useState<FetchState<T>>({ phase: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    fetcher()
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
  }, [attempt, fetcher])

  const retry = useCallback(() => {
    // Reset to loading in the event handler, not synchronously inside the
    // effect body (react-hooks/set-state-in-effect) — this is what shows
    // the spinner again for the in-flight retry.
    setState({ phase: 'loading' })
    setAttempt((n) => n + 1)
  }, [])

  return { state, retry }
}
