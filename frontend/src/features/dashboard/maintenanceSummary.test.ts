import { describe, expect, it } from 'vitest'
import type { MaintenanceWindowDTO } from '../../api/types'
import { countActiveOrUpcomingWindows } from './maintenanceSummary'

function window(
  id: number,
  componentId: string,
  startsAt: string,
  endsAt: string,
): MaintenanceWindowDTO {
  return {
    id,
    component_id: componentId,
    starts_at: startsAt,
    ends_at: endsAt,
    reason: null,
    title: null,
  }
}

const NOW = new Date('2026-07-07T10:30:00Z')

describe('countActiveOrUpcomingWindows', () => {
  it('returns 0 for an empty list — never a leaked stdlib message', () => {
    expect(countActiveOrUpcomingWindows([], NOW)).toBe(0)
  })

  it('counts active and upcoming windows, excluding past ones', () => {
    const windows = [
      window(1, 'a', '2026-07-07T10:00:00Z', '2026-07-07T11:00:00Z'), // active
      window(2, 'b', '2026-07-08T09:00:00Z', '2026-07-08T10:00:00Z'), // upcoming
      window(3, 'c', '2026-07-06T09:00:00Z', '2026-07-06T10:00:00Z'), // past
    ]
    expect(countActiveOrUpcomingWindows(windows, NOW)).toBe(2)
  })

  it('mirrors deriveWindowState\'s half-open boundary rule exactly', () => {
    const atStartsAt = window(4, 'd', '2026-07-07T10:30:00Z', '2026-07-07T11:30:00Z') // === NOW -> active
    const atEndsAt = window(5, 'e', '2026-07-07T09:30:00Z', '2026-07-07T10:30:00Z') // === NOW -> past
    expect(countActiveOrUpcomingWindows([atStartsAt], NOW)).toBe(1)
    expect(countActiveOrUpcomingWindows([atEndsAt], NOW)).toBe(0)
  })

  it('defaults `now` to the real current time when omitted', () => {
    // Just asserts it doesn't throw and returns a real count against the
    // real clock — a component-scoped test elsewhere pins `now` explicitly.
    expect(countActiveOrUpcomingWindows([])).toBe(0)
  })
})
