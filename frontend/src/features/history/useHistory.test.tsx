import { render, screen, waitFor } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_HISTORY_FRONTEND_TLS,
} from '../../mocks/handlers'
import { useHistory } from './useHistory'
import type { HistoryQuery } from './useHistory'

/** Minimal harness rendering every `useHistory` phase, mirroring how
 * `CheckHistoryPage` will drive it. */
function Harness({ query }: { query: HistoryQuery }) {
  const { state, retry } = useHistory(query)

  if (state.phase === 'loading') {
    return <div role="status">Loading…</div>
  }

  if (state.phase === 'error') {
    return (
      <div>
        <p role="alert">{state.message}</p>
        <button onClick={retry}>Retry</button>
      </div>
    )
  }

  return (
    <ul>
      {state.data.map((observation, index) => (
        <li key={index}>
          {observation.signal_key} {observation.observed_at} {observation.health}{' '}
          {String(observation.latency_ms)} {observation.location}
        </li>
      ))}
    </ul>
  )
}

const RANGE_A = { since: '2026-07-02T13:29:17.931000Z', until: '2026-07-03T13:29:17.931000Z' }
const RANGE_B = { since: '2026-06-26T13:29:17.931000Z', until: '2026-07-03T13:29:17.931000Z' }

describe('useHistory', () => {
  it('fetches the selected signal\'s observations newest-first, rendering the order exactly as returned', async () => {
    render(<Harness query={{ signalKey: 'frontend-http', range: RANGE_A }} />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(FIXTURE_HISTORY_FRONTEND_HTTP.length)
    items.forEach((item, index) => {
      expect(item).toHaveTextContent(FIXTURE_HISTORY_FRONTEND_HTTP[index].observed_at)
    })
  })

  it('reaches the error phase on failure, then recovers via retry', async () => {
    let callCount = 0
    server.use(
      http.get('/api/v1/history', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
      }),
    )

    render(<Harness query={{ signalKey: 'frontend-http', range: RANGE_A }} />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('refetches with the NEW signal_key when the selected signal changes', async () => {
    const seenSignalKeys: string[] = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        const signalKey = url.searchParams.get('signal_key') ?? ''
        seenSignalKeys.push(signalKey)
        return HttpResponse.json(
          signalKey === 'frontend-tls'
            ? FIXTURE_HISTORY_FRONTEND_TLS
            : FIXTURE_HISTORY_FRONTEND_HTTP,
        )
      }),
    )

    const { rerender } = render(
      <Harness query={{ signalKey: 'frontend-http', range: RANGE_A }} />,
    )
    await screen.findAllByRole('listitem')
    expect(seenSignalKeys).toEqual(['frontend-http'])

    rerender(<Harness query={{ signalKey: 'frontend-tls', range: RANGE_A }} />)

    await waitFor(() => {
      expect(seenSignalKeys).toEqual(['frontend-http', 'frontend-tls'])
    })

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(FIXTURE_HISTORY_FRONTEND_TLS.length)
  })

  it('refetches with the NEW tz-aware since/until when the window changes', async () => {
    const seenRanges: Array<{ since: string; until: string }> = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        seenRanges.push({
          since: url.searchParams.get('since') ?? '',
          until: url.searchParams.get('until') ?? '',
        })
        return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
      }),
    )

    const { rerender } = render(
      <Harness query={{ signalKey: 'frontend-http', range: RANGE_A }} />,
    )
    await screen.findAllByRole('listitem')
    expect(seenRanges).toEqual([RANGE_A])

    rerender(<Harness query={{ signalKey: 'frontend-http', range: RANGE_B }} />)

    await waitFor(() => {
      expect(seenRanges).toEqual([RANGE_A, RANGE_B])
    })
  })
})
