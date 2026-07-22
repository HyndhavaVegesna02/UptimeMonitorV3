import { act, renderHook, waitFor } from '@testing-library/react'
import { HttpResponse, delay, http } from 'msw'
import type { Mock } from 'vitest'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../../mocks/server'
import { useApprovalsDecisions } from './useApprovalsDecisions'

describe('useApprovalsDecisions', () => {
  let onResolved: Mock<() => void>
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    onResolved = vi.fn()
    // AC4: "a mutation never throws to the console" — proved by asserting
    // this spy stays uncalled across every scenario below.
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('starts idle for every proposal', () => {
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))
    expect(result.current.isConfirming(1)).toBe(false)
    expect(result.current.isSubmitting(1)).toBe(false)
    expect(result.current.isBlocked(1)).toBe(false)
    expect(result.current.actionFor(1)).toBeUndefined()
    expect(result.current.noticeFor(1)).toBeUndefined()
  })

  it('AC3: requestConfirm moves the proposal to confirming and blocks every other proposal', () => {
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(1, 'approve')
    })

    expect(result.current.isConfirming(1)).toBe(true)
    expect(result.current.actionFor(1)).toBe('approve')
    expect(result.current.isBlocked(1)).toBe(false)
    // Only one proposal is mid-decision at a time (AC3).
    expect(result.current.isBlocked(2)).toBe(true)
    expect(result.current.isConfirming(2)).toBe(false)
  })

  it('AC7: cancelConfirm is dismissable — resets straight back to idle', () => {
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(1, 'reject')
    })
    act(() => {
      result.current.cancelConfirm()
    })

    expect(result.current.isConfirming(1)).toBe(false)
    expect(result.current.isBlocked(2)).toBe(false)
  })

  it('AC3: confirmDecision disables (submitting) the confirming proposal while in flight', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', async () => {
        await delay(50)
        return HttpResponse.json({ proposal_id: 1, state: 'approved', resolved_at: '2026-07-21T12:06:00Z' })
      }),
    )
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(1, 'approve')
    })
    act(() => {
      void result.current.confirmDecision(1, 'approve')
    })

    expect(result.current.isSubmitting(1)).toBe(true)
    expect(result.current.isConfirming(1)).toBe(false)

    await waitFor(() => expect(result.current.isSubmitting(1)).toBe(false))
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC2/AC5: confirmDecision posts {action, actor, notes} and resolves back to idle + refreshes on success', async () => {
    let capturedBody: unknown
    server.use(
      http.post('/api/v1/decisions/:proposalId', async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json({ proposal_id: 1, state: 'approved', resolved_at: '2026-07-21T12:06:00Z' })
      }),
    )
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(1, 'approve')
    })
    await act(async () => {
      await result.current.confirmDecision(1, 'approve')
    })

    expect(capturedBody).toMatchObject({ action: 'approve' })
    expect((capturedBody as { actor: string }).actor.trim().length).toBeGreaterThan(0)
    expect(result.current.isConfirming(1)).toBe(false)
    expect(result.current.isSubmitting(1)).toBe(false)
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4: a forced 409 (already resolved / lost race) sets a non-destructive conflict notice and refreshes', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'Proposal is not open' }, { status: 409 }),
      ),
    )
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(1, 'approve')
    })
    await act(async () => {
      await result.current.confirmDecision(1, 'approve')
    })

    expect(result.current.noticeFor(1)).toMatchObject({ kind: 'conflict' })
    expect(result.current.isConfirming(1)).toBe(false)
    expect(result.current.isSubmitting(1)).toBe(false)
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4: a forced 404 (no longer exists) sets a "no longer exists" notice and refreshes', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'Proposal not found' }, { status: 404 }),
      ),
    )
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(2, 'reject')
    })
    await act(async () => {
      await result.current.confirmDecision(2, 'reject')
    })

    expect(result.current.noticeFor(2)).toMatchObject({ kind: 'gone' })
    expect(onResolved).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4: any other failure sets an inline error notice, stays confirming for retry, and does NOT refresh', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )
    const { result } = renderHook(() => useApprovalsDecisions(onResolved))

    act(() => {
      result.current.requestConfirm(1, 'approve')
    })
    await act(async () => {
      await result.current.confirmDecision(1, 'approve')
    })

    expect(result.current.noticeFor(1)).toMatchObject({ kind: 'error' })
    // Stays confirming (not idle) so a "Retry" re-attempt is possible.
    expect(result.current.isConfirming(1)).toBe(true)
    expect(result.current.isSubmitting(1)).toBe(false)
    expect(onResolved).not.toHaveBeenCalled()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
