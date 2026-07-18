import { describe, expect, it } from 'vitest'
import { formatLocationLabel } from './formatLocation'

describe('formatLocationLabel', () => {
  it('shortens a raw vendor location id to a "Location …tail" display form', () => {
    expect(formatLocationLabel('SYNTHETIC_LOCATION-0000000000000047')).toBe('Location …0047')
  })

  it('derives from the TAIL of the id, generically — no vendor-specific mapping', () => {
    // A completely different prefix shape still shortens the same way, off
    // the last 4 characters only.
    expect(formatLocationLabel('some-other-vendor-id-9981')).toBe('Location …9981')
  })

  it('returns the id unchanged when it is already at or under the tail length', () => {
    expect(formatLocationLabel('ab12')).toBe('Location …ab12')
    expect(formatLocationLabel('a')).toBe('Location …a')
  })

  it('never crashes on empty input — renders the raw (empty) string', () => {
    expect(formatLocationLabel('')).toBe('')
  })
})
