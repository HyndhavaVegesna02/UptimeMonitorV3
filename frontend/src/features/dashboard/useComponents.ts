import { useState } from 'react'
import { getComponents } from '../../api/client'
import type { ComponentDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState, UseFetchResult } from '../../lib/useFetch'

export type ComponentsFetchState = FetchState<ComponentDTO[]>

export interface UseComponentsResult extends UseFetchResult<ComponentDTO[]> {
  /** The raw ISO-UTC instant of the most recent SUCCESSFUL fetch (STORY-104
   * — the command bar's "Updated Xs ago", `RelativeTime`-ready). `undefined`
   * until the first fetch resolves. Display-layer only: a client-side
   * observation of when THIS browser last heard back, never persisted,
   * never sent to the server, and not part of the `ComponentDTO` wire
   * shape. */
  fetchedAtIso: string | undefined
}

/**
 * Fetch hook for `GET /api/v1/components` (STORY-015b AC4). Built on the
 * shared `useFetch<T>` (STORY-015c AC5) — this used to hold the fetch effect
 * itself (a discriminated-union state, a cancelled-guarded effect, an
 * `attempt`-keyed retry); that logic now lives once in `useFetch` and every
 * tab's fetch hook, including this one, is a thin wrapper over it.
 *
 * STORY-104 additively wrapped it with `fetchedAtIso`: tracked via the
 * React-documented "adjusting state when a prop changes" pattern (compare
 * against a mirrored previous-`phase` state DURING render, not inside a
 * `useEffect` — required since `eslint-plugin-react-hooks`'s
 * `set-state-in-effect` rule, DoD gate, rejects a synchronous `setState`
 * call in an effect body; the same pattern `useDismissibleBanner`/
 * `useMediaQuery` already use elsewhere in this codebase) — a fresh
 * timestamp is recorded every time `state.phase` transitions INTO
 * `'success'` (the initial load, and every successful `retry()`).
 */
export function useComponents(): UseComponentsResult {
  const result = useFetch(getComponents)
  const [fetchedAtIso, setFetchedAtIso] = useState<string | undefined>(undefined)
  const [prevPhase, setPrevPhase] = useState(result.state.phase)

  if (result.state.phase !== prevPhase) {
    setPrevPhase(result.state.phase)
    if (result.state.phase === 'success') {
      setFetchedAtIso(new Date().toISOString())
    }
  }

  return { ...result, fetchedAtIso }
}
