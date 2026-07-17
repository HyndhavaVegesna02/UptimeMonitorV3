import { useState } from 'react'
import { getComponents } from '../../api/client'
import type { ComponentDTO } from '../../api/types'
import { useFetch } from '../../lib/useFetch'
import type { FetchState, UseFetchResult } from '../../lib/useFetch'

export type ComponentsFetchState = FetchState<ComponentDTO[]>

export interface UseComponentsResult extends UseFetchResult<ComponentDTO[]> {
  /**
   * ISO-8601 instant of the most recent successful fetch (STORY-099 AC3 —
   * the Dashboard's "Updated Xs ago" header indicator, rendered through the
   * STORY-098 `RelativeTime`/`useRelativeTime`, never as a raw string
   * itself). `null` until the first successful load, and stays `null`
   * across a failure — never a fabricated/stale instant. Re-stamped on
   * EVERY later success (e.g. a manual retry), not just the first, so the
   * indicator always reflects the actual last-success time. Display-layer
   * state only — no API change.
   */
  lastUpdatedAt: string | null
}

/**
 * Fetch hook for `GET /api/v1/components` (STORY-015b AC4). Built on the
 * shared `useFetch<T>` (STORY-015c AC5) — this used to hold the fetch effect
 * itself (a discriminated-union state, a cancelled-guarded effect, an
 * `attempt`-keyed retry); that logic now lives once in `useFetch` and every
 * tab's fetch hook, including this one, is a thin wrapper over it.
 */
export function useComponents(): UseComponentsResult {
  const result = useFetch(getComponents)
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null)
  // Tracks the last `state` reference we've reacted to, so a fresh success
  // gets stamped exactly once — adjusted DURING render (the documented
  // "adjusting state when a prop/derived value changes" pattern), never
  // inside a `useEffect` body (avoids the cascading-render
  // `react-hooks/set-state-in-effect` lint rule `useFetch.ts`'s own `retry`
  // callback already steers clear of).
  const [seenState, setSeenState] = useState(result.state)

  if (result.state !== seenState) {
    setSeenState(result.state)
    if (result.state.phase === 'success') {
      setLastUpdatedAt(new Date().toISOString())
    }
  }

  return { ...result, lastUpdatedAt }
}
