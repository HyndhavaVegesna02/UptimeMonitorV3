import { act, renderHook } from '@testing-library/react'
import { beforeEach, describe, expect, it } from 'vitest'
import { SIDEBAR_COLLAPSE_STORAGE_KEY, useSidebarCollapse } from './useSidebarCollapse'

describe('useSidebarCollapse', () => {
  beforeEach(() => {
    window.localStorage.clear()
  })

  it('defaults to expanded (not collapsed) when localStorage has no stored value', () => {
    const { result } = renderHook(() => useSidebarCollapse())
    expect(result.current.collapsed).toBe(false)
  })

  it('restores a previously-persisted collapsed=true value on initial render (no flash)', () => {
    window.localStorage.setItem(SIDEBAR_COLLAPSE_STORAGE_KEY, 'true')
    const { result } = renderHook(() => useSidebarCollapse())
    expect(result.current.collapsed).toBe(true)
  })

  it('toggle flips the in-memory state and persists the new value to localStorage', () => {
    const { result } = renderHook(() => useSidebarCollapse())

    act(() => {
      result.current.toggle()
    })

    expect(result.current.collapsed).toBe(true)
    expect(window.localStorage.getItem(SIDEBAR_COLLAPSE_STORAGE_KEY)).toBe('true')

    act(() => {
      result.current.toggle()
    })

    expect(result.current.collapsed).toBe(false)
    expect(window.localStorage.getItem(SIDEBAR_COLLAPSE_STORAGE_KEY)).toBe('false')
  })

  it('a fresh hook instance restores the persisted value from a prior toggle', () => {
    const { result: first } = renderHook(() => useSidebarCollapse())
    act(() => {
      first.current.toggle()
    })

    const { result: second } = renderHook(() => useSidebarCollapse())
    expect(second.current.collapsed).toBe(true)
  })
})
