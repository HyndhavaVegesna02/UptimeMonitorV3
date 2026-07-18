import { renderHook } from '@testing-library/react'
import { act } from 'react'
import { describe, expect, it } from 'vitest'
import { useDismissibleBanner } from './useDismissibleBanner'

describe('useDismissibleBanner', () => {
  it('starts not dismissed', () => {
    const { result } = renderHook(() => useDismissibleBanner(true))
    expect(result.current.dismissed).toBe(false)
  })

  it('dismiss() sets dismissed to true', () => {
    const { result } = renderHook(() => useDismissibleBanner(true))

    act(() => result.current.dismiss())

    expect(result.current.dismissed).toBe(true)
  })

  it('restore() sets dismissed back to false', () => {
    const { result } = renderHook(() => useDismissibleBanner(true))

    act(() => result.current.dismiss())
    expect(result.current.dismissed).toBe(true)

    act(() => result.current.restore())
    expect(result.current.dismissed).toBe(false)
  })

  it('re-arms (resets dismissed) once visible cycles false -> true', () => {
    const { result, rerender } = renderHook(
      ({ visible }) => useDismissibleBanner(visible),
      { initialProps: { visible: true } },
    )

    act(() => result.current.dismiss())
    expect(result.current.dismissed).toBe(true)

    rerender({ visible: false })
    expect(result.current.dismissed).toBe(true)

    rerender({ visible: true })
    expect(result.current.dismissed).toBe(false)
  })

  it('a dismiss while visible does not reappear on an unrelated re-render (still visible=true)', () => {
    const { result, rerender } = renderHook(
      ({ visible }) => useDismissibleBanner(visible),
      { initialProps: { visible: true } },
    )

    act(() => result.current.dismiss())
    rerender({ visible: true })

    expect(result.current.dismissed).toBe(true)
  })
})
