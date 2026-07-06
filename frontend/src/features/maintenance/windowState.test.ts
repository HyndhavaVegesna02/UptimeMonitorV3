import { describe, expect, it } from 'vitest'
import { deriveWindowState } from './windowState'

const STARTS_AT = '2026-07-07T10:00:00Z'
const ENDS_AT = '2026-07-07T11:00:00Z'

describe('deriveWindowState', () => {
  it('returns "upcoming" strictly before starts_at', () => {
    const now = new Date('2026-07-07T09:59:59.999Z')
    expect(deriveWindowState(STARTS_AT, ENDS_AT, now)).toBe('upcoming')
  })

  it('returns "active" exactly AT starts_at (half-open boundary: starts_at <= now)', () => {
    const now = new Date(STARTS_AT)
    expect(deriveWindowState(STARTS_AT, ENDS_AT, now)).toBe('active')
  })

  it('returns "active" strictly between starts_at and ends_at', () => {
    const now = new Date('2026-07-07T10:30:00Z')
    expect(deriveWindowState(STARTS_AT, ENDS_AT, now)).toBe('active')
  })

  it('returns "past" exactly AT ends_at (half-open boundary: now < ends_at fails)', () => {
    const now = new Date(ENDS_AT)
    expect(deriveWindowState(STARTS_AT, ENDS_AT, now)).toBe('past')
  })

  it('returns "past" strictly after ends_at', () => {
    const now = new Date('2026-07-07T11:00:00.001Z')
    expect(deriveWindowState(STARTS_AT, ENDS_AT, now)).toBe('past')
  })
})
