import { useCallback, useEffect, useState } from 'react'

export type FetchState<T> =
  | { phase: 'loading' }
  | { phase: 'error'; message: string }
  | { phase: 'success'; data: T }

export interface UseFetchResult<T> {
  state: FetchState<T>
  retry: () => void
  /** Wall-clock time of the most recent SUCCESSFUL completion, or `null`
   * before the first one — captured inside the fetch promise's own
   * `.then()` callback (never a render-time `new Date()` read), so a
   * caller can build a "last updated" indicator without it resetting on
   * every unrelated re-render (STORY-121 quality-review fix). Stays at its
   * previous value through an `error` phase — never a fabricated success
   * time. */
  succeededAt: Date | null
}

/**
 * Generic fetch hook (STORY-121) so every shell/tab data-loading hook
 * (`useComponents`, `useApprovals`, and future tabs) shares one
 * implementation: a discriminated-union `FetchState<T>`, a
 * cancelled-guarded effect (never sets state after the request is
 * stale/unmounted), and an `attempt`-keyed `retry` that re-triggers the
 * effect via a dependency bump rather than calling the fetcher directly
 * from the event handler.
 *
 * `fetcher` must be a stable reference (a module-level function such as
 * `getComponents`/`getApprovals`, not a fresh inline closure per render) —
 * it is a `useEffect` dependency, so a fetcher that changes identity every
 * render would refetch every render.
 */
export function useFetch<T>(fetcher: () => Promise<T>): UseFetchResult<T> {
  const [state, setState] = useState<FetchState<T>>({ phase: 'loading' })
  const [succeededAt, setSucceededAt] = useState<Date | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    fetcher()
      .then((data) => {
        if (!cancelled) {
          setState({ phase: 'success', data })
          setSucceededAt(new Date())
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

  return { state, retry, succeededAt }
}
