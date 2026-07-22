import { describe, expect, it } from 'vitest'
import { localDateTimeToUtcIso } from './localDateTimeToUtcIso'

describe('localDateTimeToUtcIso', () => {
  it('converts a datetime-local wall-clock value to a tz-aware UTC ISO string (trailing Z)', () => {
    const result = localDateTimeToUtcIso('2026-07-22T10:30')
    expect(result.endsWith('Z')).toBe(true)
  })

  it('round-trips to the SAME instant `new Date(localValue)` represents — a known local input yields a Z string that re-parses to the same moment', () => {
    const local = '2026-07-22T10:30'
    const expectedMs = new Date(local).getTime()

    const result = localDateTimeToUtcIso(local)

    expect(new Date(result).getTime()).toBe(expectedMs)
  })

  it('is a pure function of its input (calling twice on the same value yields the same result)', () => {
    expect(localDateTimeToUtcIso('2026-01-01T00:00')).toBe(localDateTimeToUtcIso('2026-01-01T00:00'))
  })
})
