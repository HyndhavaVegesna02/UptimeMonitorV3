import { describe, expect, it } from 'vitest'
import { formatObservedAt } from './formatTimestamp'

describe('formatObservedAt', () => {
  it('formats an ISO observed_at as an absolute UTC date + time with an explicit UTC label (STORY-140 AC2 — consistent with the Maintenance card convention), deterministic regardless of the host timezone', () => {
    expect(formatObservedAt('2026-07-21T07:58:41.133000Z')).toBe('Jul 21, 07:58:41 UTC')
  })

  it('is stable across a year boundary (still no year shown - the grid is a recent-history window, not an archive)', () => {
    expect(formatObservedAt('2026-01-01T00:00:00.000000Z')).toBe('Jan 01, 00:00:00 UTC')
  })
})
