import { describe, expect, it } from 'vitest'
import { formatRelativeTime } from './relativeTime'

const NOW = new Date('2026-07-21T08:00:00Z')

describe('formatRelativeTime', () => {
  it('renders "just now" for anything under 5 seconds old', () => {
    expect(formatRelativeTime(new Date('2026-07-21T07:59:57Z'), NOW)).toBe('just now')
  })

  it('renders whole seconds under a minute', () => {
    expect(formatRelativeTime(new Date('2026-07-21T07:59:32Z'), NOW)).toBe('28s ago')
  })

  it('renders whole minutes under an hour', () => {
    expect(formatRelativeTime(new Date('2026-07-21T07:58:00Z'), NOW)).toBe('2 min ago')
  })

  it('renders whole hours beyond that', () => {
    expect(formatRelativeTime(new Date('2026-07-21T05:00:00Z'), NOW)).toBe('3h ago')
  })

  it('treats a future timestamp (clock skew) as "just now" rather than a negative duration', () => {
    expect(formatRelativeTime(new Date('2026-07-21T08:00:05Z'), NOW)).toBe('just now')
  })
})
