import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { TooltipGroupProvider } from './TooltipGroupProvider'
import { useTooltipGroup } from './tooltipGroupContext'

function wrapper({ children }: { children: ReactNode }) {
  return <TooltipGroupProvider>{children}</TooltipGroupProvider>
}

describe('useTooltipGroup (emil delayed-tooltip pattern)', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('is not warm for the very first tooltip in a group', () => {
    const { result } = renderHook(() => useTooltipGroup(), { wrapper })
    expect(result.current.warm).toBe(false)
  })

  it('becomes warm once a tooltip in the group has been shown, and stays warm while shown', () => {
    const { result } = renderHook(() => useTooltipGroup(), { wrapper })

    act(() => {
      result.current.markShown()
    })

    expect(result.current.warm).toBe(true)
  })

  it('stays warm for a short cooldown window after the tooltip hides, then cools down', () => {
    const { result } = renderHook(() => useTooltipGroup(), { wrapper })

    act(() => {
      result.current.markShown()
      result.current.scheduleCooldown()
    })

    // Still warm immediately after hide — a subsequent adjacent tooltip
    // should open instantly, no re-delay (emil: "skip delay on subsequent hovers").
    expect(result.current.warm).toBe(true)

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    expect(result.current.warm).toBe(false)
  })

  it('a scheduled cooldown is cancelled if the group is shown again before it fires', () => {
    const { result } = renderHook(() => useTooltipGroup(), { wrapper })

    act(() => {
      result.current.markShown()
      result.current.scheduleCooldown()
    })

    act(() => {
      vi.advanceTimersByTime(100)
      result.current.markShown()
    })

    act(() => {
      vi.advanceTimersByTime(1000)
    })

    // The second markShown cancelled the pending cooldown, so warm holds.
    expect(result.current.warm).toBe(true)
  })

  it('falls back to a standalone (never-warm) value outside a provider', () => {
    const { result } = renderHook(() => useTooltipGroup())
    expect(result.current.warm).toBe(false)
    expect(() => result.current.markShown()).not.toThrow()
    expect(() => result.current.scheduleCooldown()).not.toThrow()
  })
})
