import { describe, expect, it } from 'vitest'
import { ALL_TABS, getTabByPath, NAV_GROUPS } from './tabs'

describe('NAV_GROUPS / getTabByPath', () => {
  it('declares the six-route IA across exactly two static groups', () => {
    expect(NAV_GROUPS.map((g) => g.id)).toEqual(['monitoring', 'operations'])
    expect(ALL_TABS).toHaveLength(6)
  })

  it('finds a tab by its exact pathname', () => {
    expect(getTabByPath('/dashboard')?.label).toBe('Dashboard')
    expect(getTabByPath('/publications')?.label).toBe('Publications')
  })

  it('returns undefined for a pathname that matches no tab (e.g. /styleguide)', () => {
    expect(getTabByPath('/styleguide')).toBeUndefined()
  })
})
