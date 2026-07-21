import { describe, expect, it } from 'vitest'
import { computeWindowRange, WINDOW_OPTIONS } from './windowRange'

describe('WINDOW_OPTIONS', () => {
  it('offers exactly 24h/7d/30d, in that order', () => {
    expect(WINDOW_OPTIONS.map((option) => option.key)).toEqual(['24h', '7d', '30d'])
  })
})

describe('computeWindowRange', () => {
  // A deliberately NON-aligned "now" (odd hour, minute, second, millisecond)
  // — checklist: window/interval math must be tested on a non-clean
  // boundary, not just a round timestamp.
  const now = new Date('2026-07-21T18:37:22.481Z')

  it('computes a 24h window as [now - 24h, now], both tz-aware UTC ISO with a trailing Z', () => {
    const { since, until } = computeWindowRange('24h', now)

    expect(until).toBe('2026-07-21T18:37:22.481Z')
    expect(since).toBe('2026-07-20T18:37:22.481Z')
    expect(since.endsWith('Z')).toBe(true)
    expect(until.endsWith('Z')).toBe(true)
  })

  it('computes a 7d window as exactly 7*24h before now, non-aligned millisecond preserved', () => {
    const { since, until } = computeWindowRange('7d', now)

    expect(until).toBe(now.toISOString())
    expect(new Date(until).getTime() - new Date(since).getTime()).toBe(7 * 24 * 60 * 60 * 1000)
  })

  it('computes a 30d window as exactly 30*24h before now', () => {
    const { since, until } = computeWindowRange('30d', now)

    expect(new Date(until).getTime() - new Date(since).getTime()).toBe(30 * 24 * 60 * 60 * 1000)
  })

  it('never emits a naive (Z-less) datetime for any window option', () => {
    for (const option of WINDOW_OPTIONS) {
      const { since, until } = computeWindowRange(option.key, now)
      expect(since.endsWith('Z')).toBe(true)
      expect(until.endsWith('Z')).toBe(true)
    }
  })
})
