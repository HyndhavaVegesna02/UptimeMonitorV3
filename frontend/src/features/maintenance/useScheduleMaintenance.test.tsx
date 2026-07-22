import { act, renderHook } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import type { Mock } from 'vitest'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../../mocks/server'
import { useScheduleMaintenance } from './useScheduleMaintenance'

const VALID_VALUES = {
  componentId: 'http-check',
  startsAtLocal: '2026-07-22T10:00',
  endsAtLocal: '2026-07-22T12:00',
  title: 'Planned DB maintenance',
  reason: 'DB upgrade',
}

describe('useScheduleMaintenance', () => {
  let onScheduled: Mock<() => void>
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    onScheduled = vi.fn()
    // AC4: "mutations never throw to the console" — proved across every
    // scenario below.
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('starts idle with no field errors or form error', () => {
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))
    expect(result.current.phase).toBe('idle')
    expect(result.current.fieldErrors).toEqual({})
    expect(result.current.formError).toBeNull()
  })

  it('AC3: client-side guards ends_at <= starts_at WITHOUT even calling the API', async () => {
    let called = false
    server.use(
      http.post('/api/v1/maintenance', () => {
        called = true
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))

    let ok: boolean = true
    await act(async () => {
      ok = await result.current.submit({
        ...VALID_VALUES,
        startsAtLocal: '2026-07-22T12:00',
        endsAtLocal: '2026-07-22T10:00',
      })
    })

    expect(ok).toBe(false)
    expect(called).toBe(false)
    expect(result.current.fieldErrors.ends_at).toBeTruthy()
    expect(onScheduled).not.toHaveBeenCalled()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC3: client-side guards a blank component selection', async () => {
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))

    let ok: boolean = true
    await act(async () => {
      ok = await result.current.submit({ ...VALID_VALUES, componentId: '' })
    })

    expect(ok).toBe(false)
    expect(result.current.fieldErrors.component_id).toBeTruthy()
  })

  it('AC2: converts datetime-local values to UTC ISO and POSTs, resetting on 201 success', async () => {
    let capturedBody: unknown
    server.use(
      http.post('/api/v1/maintenance', async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json(
          { id: 4, component_id: 'http-check', starts_at: '2026-07-22T10:00:00Z', ends_at: '2026-07-22T12:00:00Z', reason: 'DB upgrade', title: 'Planned DB maintenance' },
          { status: 201 },
        )
      }),
    )
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))

    let ok = false
    await act(async () => {
      ok = await result.current.submit(VALID_VALUES)
    })

    expect(ok).toBe(true)
    expect(capturedBody).toMatchObject({
      component_id: 'http-check',
      reason: 'DB upgrade',
      title: 'Planned DB maintenance',
    })
    expect((capturedBody as { starts_at: string }).starts_at.endsWith('Z')).toBe(true)
    expect((capturedBody as { ends_at: string }).ends_at.endsWith('Z')).toBe(true)
    expect(result.current.phase).toBe('idle')
    expect(onScheduled).toHaveBeenCalledTimes(1)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('sends null (not empty strings) for blank optional title/reason', async () => {
    let capturedBody: unknown
    server.use(
      http.post('/api/v1/maintenance', async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json({}, { status: 201 })
      }),
    )
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))

    await act(async () => {
      await result.current.submit({ ...VALID_VALUES, title: '  ', reason: '' })
    })

    expect(capturedBody).toMatchObject({ title: null, reason: null })
  })

  it('CRUX AC3: a forced end-before-start 422 from the server maps to the ends_at field (not starts_at)', async () => {
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'ends_at must be strictly greater than starts_at.' }, { status: 422 }),
      ),
    )
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))

    let ok = true
    await act(async () => {
      // Values are client-valid (end after start) so the guard doesn't
      // short-circuit before the server round-trip — this forces the REAL
      // 422 path.
      ok = await result.current.submit(VALID_VALUES)
    })

    expect(ok).toBe(false)
    expect(result.current.fieldErrors.ends_at).toBe('ends_at must be strictly greater than starts_at.')
    expect(result.current.fieldErrors.starts_at).toBeUndefined()
    expect(result.current.formError).toBeNull()
    expect(onScheduled).not.toHaveBeenCalled()
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('a 422 detail naming none of the fields falls back to a form-level banner', async () => {
    server.use(
      http.post('/api/v1/maintenance', () => HttpResponse.json({ detail: 'Internal server error' }, { status: 422 })),
    )
    const { result } = renderHook(() => useScheduleMaintenance(onScheduled))

    await act(async () => {
      await result.current.submit(VALID_VALUES)
    })

    expect(result.current.formError).toBe('Internal server error')
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })
})
