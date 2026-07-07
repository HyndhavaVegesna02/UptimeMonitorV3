import { beforeEach, describe, expect, it } from 'vitest'
import {
  SIDEBAR_STORAGE_KEY,
  persistExpanded,
  resolveInitialExpanded,
} from './sidebarState'

describe('sidebarState', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to expanded when nothing is persisted', () => {
    expect(resolveInitialExpanded()).toBe(true)
  })

  it('persists a collapsed choice and resolves it back on the next read', () => {
    persistExpanded(false)
    expect(window.localStorage.getItem(SIDEBAR_STORAGE_KEY)).toBe('false')
    expect(resolveInitialExpanded()).toBe(false)
  })

  it('persists an expanded choice and resolves it back on the next read', () => {
    persistExpanded(false)
    persistExpanded(true)
    expect(resolveInitialExpanded()).toBe(true)
  })

  it('falls back to the expanded default when the stored value is corrupt', () => {
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, 'not-a-boolean')
    expect(resolveInitialExpanded()).toBe(true)
  })
})
