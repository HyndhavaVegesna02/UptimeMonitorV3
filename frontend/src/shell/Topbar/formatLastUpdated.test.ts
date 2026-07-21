import { describe, expect, it } from 'vitest'
import { formatLastUpdated } from './formatLastUpdated'

const NOW = new Date('2026-07-21T12:10:00Z')

describe('formatLastUpdated', () => {
  it('renders a still-loading placeholder when there is no successful fetch yet', () => {
    expect(formatLastUpdated(null, NOW)).toBe('Updating…')
  })

  it('renders "just now" for anything under a minute old', () => {
    expect(formatLastUpdated(new Date('2026-07-21T12:09:45Z'), NOW)).toBe('Updated just now')
  })

  it('renders the singular "1m ago" for exactly one elapsed minute', () => {
    expect(formatLastUpdated(new Date('2026-07-21T12:09:00Z'), NOW)).toBe('Updated 1m ago')
  })

  it('renders plural minutes under an hour', () => {
    expect(formatLastUpdated(new Date('2026-07-21T11:55:00Z'), NOW)).toBe('Updated 15m ago')
  })

  it('renders the singular "1h ago" for exactly one elapsed hour', () => {
    expect(formatLastUpdated(new Date('2026-07-21T11:10:00Z'), NOW)).toBe('Updated 1h ago')
  })

  it('renders plural hours beyond that', () => {
    expect(formatLastUpdated(new Date('2026-07-21T09:00:00Z'), NOW)).toBe('Updated 3h ago')
  })
})
