import { useCallback, useEffect, useState } from 'react'
import { dedupedFetch, forgetFetch } from './fetchDedup'

/** Default request timeout (STORY-136 AC3) — a never-settling request (a
 * hung network call, a backend that never responds) transitions to the
 * `error` phase instead of leaving the caller spinning forever. Chosen as a
 * generous ceiling for the shell's own fetches (components/approvals) well
 * above any real observed latency, while still bounding the worst case.
 * Overridable per call site via `useFetch`'s second argument. */
export const DEFAULT_FETCH_TIMEOUT_MS = 15_000

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
 *
 * `timeoutMs` (STORY-136 AC3, default `DEFAULT_FETCH_TIMEOUT_MS`) bounds how
 * long a request may stay in the `loading` phase: if neither `.then()` nor
 * `.catch()` has fired by then, the hook forces the `error` phase itself
 * (surfacing the existing `ErrorState` + retry) rather than leaving the
 * caller spinning on a hung request forever. The timer is cleared the
 * moment the real fetch settles, on unmount, and on every retry, so it never
 * fires against a request that already resolved.
 *
 * The actual fetch is issued via `dedupedFetch` (STORY-137), not `fetcher()`
 * directly: two `useFetch` instances that share the same stable fetcher
 * reference (e.g. the shell and the Dashboard page both calling the
 * module-level `getComponents`) and happen to be in flight at the same
 * moment share ONE underlying network request instead of firing one each.
 * This is pure promise-coalescing, not a result cache — see
 * `fetchDedup.ts` — so `retry` always genuinely re-invokes the fetcher once
 * the shared request has settled.
 */
export function useFetch<T>(
  fetcher: () => Promise<T>,
  timeoutMs: number = DEFAULT_FETCH_TIMEOUT_MS,
): UseFetchResult<T> {
  const [state, setState] = useState<FetchState<T>>({ phase: 'loading' })
  const [succeededAt, setSucceededAt] = useState<Date | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    const timeoutId = setTimeout(() => {
      if (!cancelled) {
        cancelled = true
        // A never-settling fetcher would otherwise leave a permanent
        // `dedupedFetch` in-flight entry behind (STORY-137) — evict it so
        // the next `retry` genuinely re-issues a request instead of
        // silently rejoining the same still-hung promise.
        forgetFetch(fetcher)
        setState({ phase: 'error', message: 'Request timed out' })
      }
    }, timeoutMs)

    dedupedFetch(fetcher)
      .then((data) => {
        if (!cancelled) {
          cancelled = true
          clearTimeout(timeoutId)
          setState({ phase: 'success', data })
          setSucceededAt(new Date())
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          cancelled = true
          clearTimeout(timeoutId)
          setState({
            phase: 'error',
            message: err instanceof Error ? err.message : 'Unknown error',
          })
        }
      })

    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }
  }, [attempt, fetcher, timeoutMs])

  const retry = useCallback(() => {
    // Reset to loading in the event handler, not synchronously inside the
    // effect body (react-hooks/set-state-in-effect) — this is what shows
    // the spinner again for the in-flight retry.
    setState({ phase: 'loading' })
    setAttempt((n) => n + 1)
  }, [])

  return { state, retry, succeededAt }
}
