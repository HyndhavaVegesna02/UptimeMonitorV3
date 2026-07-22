import { describe, expect, it } from 'vitest'
import type { ComponentDTO } from '../api/types'
import { derivePageTitle } from './derivePageTitle'

const COMPONENTS: ComponentDTO[] = [
  { id: 'http-check', name: 'HTTP Check', status: 'operational' },
]

describe('derivePageTitle', () => {
  it('uses the static tab label for a known nav route', () => {
    expect(derivePageTitle('/availability', COMPONENTS)).toBe('Availability')
    expect(derivePageTitle('/dashboard', COMPONENTS)).toBe('Dashboard')
  })

  it('uses the matching component name for a component-scoped availability route (STORY-143 AC1)', () => {
    expect(derivePageTitle('/availability/http-check', COMPONENTS)).toBe('HTTP Check')
  })

  it('falls back to the "Availability" tab label when the scoped id has no match yet (loading) or is unknown', () => {
    expect(derivePageTitle('/availability/does-not-exist', COMPONENTS)).toBe('Availability')
    expect(derivePageTitle('/availability/http-check', [])).toBe('Availability')
  })

  it('falls back to "Dashboard" for a completely unmatched path (existing redirect-to-dashboard behavior)', () => {
    expect(derivePageTitle('/nope', COMPONENTS)).toBe('Dashboard')
  })
})
