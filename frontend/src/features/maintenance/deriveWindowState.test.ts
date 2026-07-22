import { describe, expect, it } from 'vitest'
import { deriveMaintenanceWindowState } from './deriveWindowState'

const WINDOW = { starts_at: '2026-07-22T00:00:00Z', ends_at: '2026-07-22T02:00:00Z' }

describe('deriveMaintenanceWindowState', () => {
  it('AC1: before starts_at -> upcoming', () => {
    expect(deriveMaintenanceWindowState(WINDOW, new Date('2026-07-21T23:59:59Z'))).toBe('upcoming')
  })

  it('AC1: strictly between starts_at and ends_at -> active', () => {
    expect(deriveMaintenanceWindowState(WINDOW, new Date('2026-07-22T01:00:00Z'))).toBe('active')
  })

  it('AC1: at or after ends_at -> past', () => {
    expect(deriveMaintenanceWindowState(WINDOW, new Date('2026-07-22T02:00:01Z'))).toBe('past')
  })

  it('AC1 boundary (pinned): now === starts_at is ACTIVE, not upcoming (half-open [starts_at, ends_at))', () => {
    expect(deriveMaintenanceWindowState(WINDOW, new Date('2026-07-22T00:00:00Z'))).toBe('active')
  })

  it('AC1 boundary (pinned): now === ends_at is PAST, not active (half-open [starts_at, ends_at))', () => {
    expect(deriveMaintenanceWindowState(WINDOW, new Date('2026-07-22T02:00:00Z'))).toBe('past')
  })
})
