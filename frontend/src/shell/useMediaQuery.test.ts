import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useMediaQuery } from './useMediaQuery'

/** A minimal fake `MediaQueryList` so tests can flip the match state and
 * fire the 'change' listener React subscribes to (jsdom's real
 * `matchMedia` never re-evaluates on a mocked width). */
function makeFakeMediaQueryList(initialMatches: boolean) {
  let matches = initialMatches
  const listeners = new Set<(event: { matches: boolean }) => void>()
  return {
    get matches() {
      return matches
    },
    addEventListener: (_: 'change', listener: (event: { matches: boolean }) => void) => {
      listeners.add(listener)
    },
    removeEventListener: (_: 'change', listener: (event: { matches: boolean }) => void) => {
      listeners.delete(listener)
    },
    setMatches(next: boolean) {
      matches = next
      for (const listener of listeners) {
        listener({ matches: next })
      }
    },
  }
}

describe('useMediaQuery', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns the current match state from matchMedia on initial render', () => {
    const fake = makeFakeMediaQueryList(true)
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue(fake))

    const { result } = renderHook(() => useMediaQuery('(min-width: 861px)'))
    expect(result.current).toBe(true)
  })

  it('updates when the media query match state changes', () => {
    const fake = makeFakeMediaQueryList(false)
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue(fake))

    const { result } = renderHook(() => useMediaQuery('(min-width: 861px)'))
    expect(result.current).toBe(false)

    act(() => {
      fake.setMatches(true)
    })

    expect(result.current).toBe(true)
  })
})
