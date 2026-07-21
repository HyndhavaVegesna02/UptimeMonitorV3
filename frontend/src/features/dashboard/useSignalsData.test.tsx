import { renderHook, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { FIXTURE_AVAILABILITY } from '../../mocks/handlers/availability'
import { FIXTURE_HISTORY } from '../../mocks/handlers/history'
import { server } from '../../mocks/server'
import type { FetchState } from '../../lib/useFetch'
import { useSignalsData } from './useSignalsData'

describe('useSignalsData', () => {
  it('stays loading while the components fetch is loading', () => {
    const { result } = renderHook(() => useSignalsData({ phase: 'loading' }))
    expect(result.current.phase).toBe('loading')
  })

  it('propagates a components-fetch error rather than attempting any signal fetch', () => {
    const { result } = renderHook(() => useSignalsData({ phase: 'error', message: 'boom' }))
    expect(result.current).toEqual({ phase: 'error', message: 'boom' })
  })

  it('resolves to an empty map immediately for zero components (no signal_key to query)', async () => {
    const { result } = renderHook(() =>
      useSignalsData({ phase: 'success', data: [] } as FetchState<{ id: string; name: string; status: string }[]>),
    )
    await waitFor(() => expect(result.current.phase).toBe('success'))
    expect(result.current).toEqual({ phase: 'success', data: {} })
  })

  it('fetches history + availability for each component id, in parallel, keyed by that id', async () => {
    const { result } = renderHook(() =>
      useSignalsData({
        phase: 'success',
        data: [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }],
      }),
    )

    await waitFor(() => expect(result.current.phase).toBe('success'))
    if (result.current.phase !== 'success') throw new Error('expected success')

    expect(result.current.data['http-check'].history).toEqual(FIXTURE_HISTORY['http-check'])
    expect(result.current.data['http-check'].availability).toEqual(FIXTURE_AVAILABILITY['http-check'])
  })

  it('resolves an error phase when a per-signal fetch fails', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))

    const { result } = renderHook(() =>
      useSignalsData({
        phase: 'success',
        data: [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }],
      }),
    )

    await waitFor(() => expect(result.current.phase).toBe('error'))
  })

  it('re-fetches when the component id set changes', async () => {
    const { result, rerender } = renderHook(
      ({ components }) => useSignalsData({ phase: 'success', data: components }),
      { initialProps: { components: [{ id: 'http-check', name: 'HTTP Check', status: 'operational' }] } },
    )
    await waitFor(() => expect(result.current.phase).toBe('success'))

    rerender({ components: [] })
    await waitFor(() => {
      if (result.current.phase !== 'success') throw new Error('not yet success')
      expect(result.current.data).toEqual({})
    })
  })
})
