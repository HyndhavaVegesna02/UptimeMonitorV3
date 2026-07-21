import { describe, expect, it } from 'vitest'
import type { FetchState } from './useFetch'
import { combineFetchPhase, firstErrorMessage } from './combineFetchStates'

describe('combineFetchPhase', () => {
  it('is "success" only when every state has succeeded', () => {
    const states: FetchState<number>[] = [{ phase: 'success', data: 1 }, { phase: 'success', data: 2 }]
    expect(combineFetchPhase(states)).toBe('success')
  })

  it('is "loading" when any state is still loading and none have errored', () => {
    const states: FetchState<number>[] = [{ phase: 'success', data: 1 }, { phase: 'loading' }]
    expect(combineFetchPhase(states)).toBe('loading')
  })

  it('is "error" when any state has errored, even if others are still loading', () => {
    const states: FetchState<number>[] = [{ phase: 'loading' }, { phase: 'error', message: 'boom' }]
    expect(combineFetchPhase(states)).toBe('error')
  })
})

describe('firstErrorMessage', () => {
  it('returns the first error message found', () => {
    const states: FetchState<number>[] = [
      { phase: 'success', data: 1 },
      { phase: 'error', message: 'first boom' },
      { phase: 'error', message: 'second boom' },
    ]
    expect(firstErrorMessage(states)).toBe('first boom')
  })

  it('returns undefined when nothing has errored', () => {
    expect(firstErrorMessage([{ phase: 'success', data: 1 }])).toBeUndefined()
  })
})
