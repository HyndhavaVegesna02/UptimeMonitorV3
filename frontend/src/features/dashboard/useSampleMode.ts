import { useCallback, useState } from 'react'
import { ApiError, getSampleMode, putSampleMode } from '../../api/client'
import { useFetch } from '../../lib/useFetch'
import type { FetchState } from '../../lib/useFetch'

export interface UseSampleModeResult {
  /** The initial GET's read state (loading | error | success). */
  state: FetchState<{ enabled: boolean }>
  /** Re-attempts the initial GET (from the shared `useFetch`); also clears
   * any prior PUT override/error so a fresh load starts clean. */
  retry: () => void
  /** The current flag value once loaded (`undefined` before `state` reaches
   * `success`) — the GET-loaded value, or the PUT RESPONSE's value once a
   * toggle has succeeded (never optimistically, per AC2). Derived on every
   * render (not effect-synced) so there is no flash of a stale/default
   * value on load. */
  enabled: boolean | undefined
  /** PUTs the requested value. On success, `enabled` reflects the response
   * and `mutationError` is cleared. On failure, `enabled` is left unchanged
   * and `mutationError` is set; the returned promise never rejects —
   * callers read `mutationError` rather than catching. */
  setEnabled: (next: boolean) => Promise<void>
  /** True for the duration of an in-flight PUT — callers disable the switch
   * control while this is true (AC2). */
  mutating: boolean
  mutationError: string | null
}

/**
 * Feature hook for the Dashboard's sample-mode toggle (STORY-049 AC1, AC2):
 * loads the flag via the shared `useFetch(getSampleMode)`, then exposes
 * `setEnabled` to PUT a new value. `enabled` is computed on every render as
 * "the last-known-good value" — the GET's data, overridden by the most
 * recent successful PUT's response — rather than mirrored into state via an
 * effect, so there is no render where `state.phase === 'success'` but
 * `enabled` still shows a stale default. THIS IS A TEMPORARY FEATURE — see
 * `docs/scrum/wiki/sample-mode.md`'s REMOVAL inventory.
 */
export function useSampleMode(): UseSampleModeResult {
  const { state, retry } = useFetch(getSampleMode)
  const [override, setOverride] = useState<boolean | null>(null)
  const [mutating, setMutating] = useState(false)
  const [mutationError, setMutationError] = useState<string | null>(null)

  const enabled = state.phase === 'success' ? (override ?? state.data.enabled) : undefined

  const setEnabled = useCallback(async (next: boolean) => {
    setMutating(true)
    setMutationError(null)
    try {
      const result = await putSampleMode(next)
      setOverride(result.enabled)
    } catch (err) {
      setMutationError(
        err instanceof ApiError ? err.message : 'Could not update sample mode',
      )
    } finally {
      setMutating(false)
    }
  }, [])

  const retryFromScratch = useCallback(() => {
    setOverride(null)
    setMutationError(null)
    retry()
  }, [retry])

  return { state, retry: retryFromScratch, enabled, setEnabled, mutating, mutationError }
}
