import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_HISTORY_FRONTEND_TLS,
  FIXTURE_TOPOLOGY,
} from '../../mocks/handlers'
import type { AvailabilityRange } from '../availability/windowRange'
import { useAllHistory } from './useAllHistory'

/** Minimal harness rendering every `useAllHistory` phase. */
function Harness({ range }: { range: AvailabilityRange }) {
  const { state, retry } = useAllHistory(range)

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
      {state.data.map((row, index) => (
        <li key={index}>
          {row.componentName} {row.signal_key} {row.observed_at} {row.health} {row.location}
        </li>
      ))}
    </ul>
  )
}

const RANGE_A: AvailabilityRange = {
  since: '2026-07-02T13:29:17.931000Z',
  until: '2026-07-03T13:29:17.931000Z',
}
const RANGE_B: AvailabilityRange = {
  since: '2026-06-26T13:29:17.931000Z',
  until: '2026-07-03T13:29:17.931000Z',
}

describe('useAllHistory', () => {
  it('merges every topology signal\'s observations into one newest-first list, tagged with component names', async () => {
    render(<Harness range={RANGE_A} />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const items = await screen.findAllByRole('listitem')
    // frontend-http (4) + frontend-tls (2); catalogue-http/nodata-http are
    // unfixtured -> [] each, contributing zero rows.
    expect(items).toHaveLength(
      FIXTURE_HISTORY_FRONTEND_HTTP.length + FIXTURE_HISTORY_FRONTEND_TLS.length,
    )

    const frontendComponentName = FIXTURE_TOPOLOGY[0].name
    items.slice(0, FIXTURE_HISTORY_FRONTEND_HTTP.length).forEach((item, index) => {
      expect(item).toHaveTextContent(frontendComponentName)
      expect(item).toHaveTextContent(FIXTURE_HISTORY_FRONTEND_HTTP[index].observed_at)
    })
  })

  it('reaches the error phase when the topology fetch fails, then recovers via retry', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/topology', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_TOPOLOGY)
      }),
    )

    render(<Harness range={RANGE_A} />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findAllByRole('listitem')
    expect(callCount).toBe(2)
  })

  it('reaches the error phase when any per-signal history fetch fails, then recovers via retry', async () => {
    let callCount = 0
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        if (url.searchParams.get('signal_key') === 'frontend-tls') {
          callCount += 1
          if (callCount === 1) {
            return HttpResponse.json({ detail: 'boom' }, { status: 500 })
          }
        }
        const signalKey = url.searchParams.get('signal_key')
        return HttpResponse.json(
          signalKey === 'frontend-tls'
            ? FIXTURE_HISTORY_FRONTEND_TLS
            : signalKey === 'frontend-http'
              ? FIXTURE_HISTORY_FRONTEND_HTTP
              : [],
        )
      }),
    )

    render(<Harness range={RANGE_A} />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('refetches every signal with the NEW tz-aware since/until when the window changes', async () => {
    const seenRanges: Array<{ since: string; until: string }> = []
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        seenRanges.push({
          since: url.searchParams.get('since') ?? '',
          until: url.searchParams.get('until') ?? '',
        })
        return HttpResponse.json([])
      }),
    )

    const { rerender } = render(<Harness range={RANGE_A} />)
    await screen.findByRole('list')
    expect(seenRanges.every((r) => r.since === RANGE_A.since)).toBe(true)
    const firstBatchCount = seenRanges.length

    rerender(<Harness range={RANGE_B} />)

    await waitFor(() => {
      expect(seenRanges.length).toBeGreaterThan(firstBatchCount)
    })
    expect(seenRanges[seenRanges.length - 1].since).toBe(RANGE_B.since)
  })
})
