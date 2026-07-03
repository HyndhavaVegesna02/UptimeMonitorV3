import { describe, expect, it } from 'vitest'
import { windowToRange } from './windowRange'

describe('windowToRange', () => {
  const now = new Date('2026-07-03T12:00:00.000Z')

  it('24h preset: until = now, since = now - 24h', () => {
    const { since, until } = windowToRange('24h', now)
    expect(until).toBe('2026-07-03T12:00:00.000Z')
    expect(since).toBe('2026-07-02T12:00:00.000Z')
  })

  it('7d preset: since = now - 7 days', () => {
    const { since, until } = windowToRange('7d', now)
    expect(until).toBe('2026-07-03T12:00:00.000Z')
    expect(since).toBe('2026-06-26T12:00:00.000Z')
  })

  it('30d preset: since = now - 30 days', () => {
    const { since, until } = windowToRange('30d', now)
    expect(until).toBe('2026-07-03T12:00:00.000Z')
    expect(since).toBe('2026-06-03T12:00:00.000Z')
  })

  it('defaults `now` to the current time when omitted', () => {
    const before = Date.now()
    const { until } = windowToRange('24h')
    const after = Date.now()

    const untilMs = new Date(until).getTime()
    expect(untilMs).toBeGreaterThanOrEqual(before)
    expect(untilMs).toBeLessThanOrEqual(after)
  })

  it('every preset returns tz-aware UTC ISO strings (trailing Z) — the tz-discipline seam; a naive string here would 422 on the backend', () => {
    for (const preset of ['24h', '7d', '30d'] as const) {
      const { since, until } = windowToRange(preset, now)

      expect(since).toMatch(/Z$/)
      expect(until).toMatch(/Z$/)
      expect(new Date(since).toString()).not.toBe('Invalid Date')
      expect(new Date(until).toString()).not.toBe('Invalid Date')
    }
  })

  it('since is always strictly before until', () => {
    for (const preset of ['24h', '7d', '30d'] as const) {
      const { since, until } = windowToRange(preset, now)
      expect(new Date(since).getTime()).toBeLessThan(new Date(until).getTime())
    }
  })
})
