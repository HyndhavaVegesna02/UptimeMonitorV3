import { describe, expect, it } from 'vitest'
import { formatWindowRange } from './formatWindowRange'

describe('formatWindowRange', () => {
  it('formats a same-day window as "Mon D · HH:MM–HH:MM UTC"', () => {
    expect(formatWindowRange('2026-07-22T00:00:00Z', '2026-07-22T02:00:00Z')).toBe(
      'Jul 22 · 00:00–02:00 UTC',
    )
  })

  it('includes both dates when the window spans multiple days', () => {
    expect(formatWindowRange('2026-07-22T23:00:00Z', '2026-07-23T01:00:00Z')).toBe(
      'Jul 22, 23:00 – Jul 23, 01:00 UTC',
    )
  })
})
