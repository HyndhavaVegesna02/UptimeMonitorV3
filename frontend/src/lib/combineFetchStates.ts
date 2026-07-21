import type { FetchState } from './useFetch'

export type CombinedPhase = 'loading' | 'error' | 'success'

/**
 * Combines several independent `useFetch` states into one region-level
 * phase (STORY-122) — a region fed by N parallel fetches (e.g. the KPI
 * row's components + approvals + signals) is "error" if any errored,
 * "loading" while any is still in flight (and none have errored), and
 * "success" only once every one has.
 */
export function combineFetchPhase(states: FetchState<unknown>[]): CombinedPhase {
  if (states.some((state) => state.phase === 'error')) {
    return 'error'
  }
  if (states.some((state) => state.phase === 'loading')) {
    return 'loading'
  }
  return 'success'
}

/** The first error message among the given states, or `undefined` if none
 * have errored. */
export function firstErrorMessage(states: FetchState<unknown>[]): string | undefined {
  for (const state of states) {
    if (state.phase === 'error') {
      return state.message
    }
  }
  return undefined
}
