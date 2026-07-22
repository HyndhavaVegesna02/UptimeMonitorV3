import { act, renderHook, waitFor } from '@testing-library/react'
import { HttpResponse, delay, http } from 'msw'
import type { Mock } from 'vitest'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../../mocks/server'
import { useMaintenanceDeletion } from './useMaintenanceDeletion'

describe('useMaintenanceDeletion', () => {
  let onResolved: Mock<() => void>
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    onResolved = vi.fn()
    // AC4: "mutations never throw to the console" — proved across scenarios.
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('starts idle for every window', () => {
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))
    expect(result.current.isConfirming(1)).toBe(false)
    expect(result.current.isSubmitting(1)).toBe(false)
    expect(result.current.isBlocked(1)).toBe(false)
    expect(result.current.noticeFor(1)).toBeUndefined()
  })

  it('AC4: requestConfirm moves the window to confirming and blocks every other window', () => {
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))

    act(() => {
      result.current.requestConfirm(1)
    })

    expect(result.current.isConfirming(1)).toBe(true)
    expect(result.current.isBlocked(2)).toBe(true)
    expect(result.current.isConfirming(2)).toBe(false)
  })

  it('cancelConfirm is dismissable — resets straight back to idle', () => {
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))

    act(() => {
      result.current.requestConfirm(1)
    })
    act(() => {
      result.current.cancelConfirm()
    })

    expect(result.current.isConfirming(1)).toBe(false)
    expect(result.current.isBlocked(2)).toBe(false)
  })

  it('confirmDelete disables (submitting) the confirming window while in flight', async () => {
    server.use(
      http.delete('/api/v1/maintenance/:windowId', async () => {
        await delay(50)
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))

    act(() => {
      result.current.requestConfirm(1)
    })
    act(() => {
      void result.current.confirmDelete(1)
    })

    expect(result.current.isSubmitting(1)).toBe(true)
    expect(result.current.isConfirming(1)).toBe(false)

    await waitFor(() => expect(result.current.isSubmitting(1)).toBe(false))
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4: confirmDelete DELETEs and resolves back to idle + refreshes on 204 success', async () => {
    let capturedUrl: string | undefined
    server.use(
      http.delete('/api/v1/maintenance/:windowId', ({ request }) => {
        capturedUrl = request.url
        return new HttpResponse(null, { status: 204 })
      }),
    )
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))

    act(() => {
      result.current.requestConfirm(4)
    })
    await act(async () => {
      await result.current.confirmDelete(4)
    })

    expect(capturedUrl).toContain('/v1/maintenance/4')
    expect(result.current.isConfirming(4)).toBe(false)
    expect(result.current.isSubmitting(4)).toBe(false)
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4/AC7 CRUX: a forced 404 (already gone) sets a non-destructive notice and STILL refreshes (not a silent success)', async () => {
    server.use(
      http.delete('/api/v1/maintenance/:windowId', () =>
        HttpResponse.json({ detail: 'Maintenance window not found' }, { status: 404 }),
      ),
    )
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))

    act(() => {
      result.current.requestConfirm(4)
    })
    await act(async () => {
      await result.current.confirmDelete(4)
    })

    expect(result.current.noticeFor(4)).toMatchObject({ kind: 'gone' })
    expect(result.current.isConfirming(4)).toBe(false)
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('any other failure sets an inline error notice, stays confirming for retry, and does NOT refresh', async () => {
    server.use(
      http.delete('/api/v1/maintenance/:windowId', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )
    const { result } = renderHook(() => useMaintenanceDeletion(onResolved))

    act(() => {
      result.current.requestConfirm(4)
    })
    await act(async () => {
      await result.current.confirmDelete(4)
    })

    expect(result.current.noticeFor(4)).toMatchObject({ kind: 'error' })
    expect(result.current.isConfirming(4)).toBe(true)
    expect(onResolved).not.toHaveBeenCalled()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
