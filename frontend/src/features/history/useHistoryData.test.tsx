import { renderHook, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import type { ComponentTopologyDTO } from '../../api/types'
import type { FetchState } from '../../lib/useFetch'
import { FIXTURE_HISTORY } from '../../mocks/handlers/history'
import { server } from '../../mocks/server'
import { useHistoryData } from './useHistoryData'

const SINCE = '2026-07-20T18:20:42.000Z'
const UNTIL = '2026-07-21T18:20:42.000Z'

const ONE_COMPONENT: ComponentTopologyDTO[] = [
  {
    id: 'http-check',
    name: 'HTTP Check',
    signals: [{ signal_key: 'http-check', name: 'HTTP Check', interval_seconds: 120, component_id: 'http-check' }],
  },
]

describe('useHistoryData', () => {
  it('stays loading while the topology fetch is loading', () => {
    const { result } = renderHook(() => useHistoryData({ phase: 'loading' }, SINCE, UNTIL))
    expect(result.current.phase).toBe('loading')
  })

  it('propagates a topology-fetch error rather than attempting any per-signal fetch', () => {
    const { result } = renderHook(() => useHistoryData({ phase: 'error', message: 'boom' }, SINCE, UNTIL))
    expect(result.current).toEqual({ phase: 'error', message: 'boom' })
  })

  it('resolves an empty map immediately for zero signals (no signal_key to query)', async () => {
    const { result } = renderHook(() =>
      useHistoryData({ phase: 'success', data: [] } as FetchState<ComponentTopologyDTO[]>, SINCE, UNTIL),
    )
    await waitFor(() => expect(result.current.phase).toBe('success'))
    expect(result.current).toEqual({ phase: 'success', data: {} })
  })

  it('fetches windowed history for every signal, in parallel, keyed by signal_key', async () => {
    const { result } = renderHook(() =>
      useHistoryData({ phase: 'success', data: ONE_COMPONENT }, SINCE, UNTIL),
    )

    await waitFor(() => expect(result.current.phase).toBe('success'))
    if (result.current.phase !== 'success') throw new Error('expected success')
    expect(result.current.data['http-check']).toEqual(FIXTURE_HISTORY['http-check'])
  })

  it('sends since/until as query params on every per-signal request', async () => {
    const seenUrls: string[] = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        seenUrls.push(request.url)
        return HttpResponse.json(FIXTURE_HISTORY['http-check'])
      }),
    )

    renderHook(() => useHistoryData({ phase: 'success', data: ONE_COMPONENT }, SINCE, UNTIL))

    await waitFor(() => expect(seenUrls.length).toBeGreaterThan(0))
    const url = new URL(seenUrls[0])
    expect(url.searchParams.get('since')).toBe(SINCE)
    expect(url.searchParams.get('until')).toBe(UNTIL)
  })

  it('resolves an error phase when a per-signal fetch fails', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))

    const { result } = renderHook(() =>
      useHistoryData({ phase: 'success', data: ONE_COMPONENT }, SINCE, UNTIL),
    )

    await waitFor(() => expect(result.current.phase).toBe('error'))
  })

  it('refetches when since/until change (the window toggle is the only refetching control)', async () => {
    const seenUrls: string[] = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        seenUrls.push(request.url)
        return HttpResponse.json(FIXTURE_HISTORY['http-check'])
      }),
    )

    const { result, rerender } = renderHook(
      ({ since, until }) => useHistoryData({ phase: 'success', data: ONE_COMPONENT }, since, until),
      { initialProps: { since: SINCE, until: UNTIL } },
    )
    await waitFor(() => expect(result.current.phase).toBe('success'))
    const countAfterFirst = seenUrls.length

    rerender({ since: '2026-07-14T18:20:42.000Z', until: UNTIL })

    await waitFor(() => expect(seenUrls.length).toBeGreaterThan(countAfterFirst))
  })
})
