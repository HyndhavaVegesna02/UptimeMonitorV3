import { describe, expect, it } from 'vitest'
import { locationLabel } from './locationLabel'

describe('locationLabel', () => {
  it('shortens a real synthetic-location id to a readable "#" + last-4-digits short-id presentation (STORY-140 AC3 — an ellipsis reads as "truncated, more hidden"; "#0060" reads as a deliberate short id, the same idiom as a ticket/PR number)', () => {
    expect(locationLabel('SYNTHETIC_LOCATION-0000000000000060')).toBe('#0060')
    expect(locationLabel('SYNTHETIC_LOCATION-0000000000000047')).toBe('#0047')
  })

  it('returns the raw string unchanged when it is already 4 characters or shorter', () => {
    expect(locationLabel('ABCD')).toBe('ABCD')
    expect(locationLabel('')).toBe('')
  })
})
