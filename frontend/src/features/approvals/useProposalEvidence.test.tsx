import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import type { ObservationDTO } from '../../api/types'
import { latestPerLocation, useProposalEvidence } from './useProposalEvidence'

function makeObservation(overrides: Partial<ObservationDTO> = {}): ObservationDTO {
  return {
    signal_key: 'http-check',
    observed_at: '2026-07-17T10:00:00.000Z',
    health: 'up',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    latency_ms: 200,
    response_status_code: 200,
    check_type: 'http',
    ...overrides,
  }
}

const TWO_LOCATIONS: ObservationDTO[] = [
  makeObservation({
    observed_at: '2026-07-17T10:05:00.000Z',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    health: 'up',
    latency_ms: 210,
  }),
  makeObservation({
    observed_at: '2026-07-17T10:04:00.000Z',
    location: 'SYNTHETIC_LOCATION-0000000000000061',
    health: 'degraded',
    latency_ms: 900,
  }),
  makeObservation({
    observed_at: '2026-07-17T09:59:00.000Z',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    health: 'down',
    latency_ms: null,
  }),
]

const SINGLE_LOCATION: ObservationDTO[] = [
  makeObservation({
    observed_at: '2026-07-17T10:05:00.000Z',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    health: 'up',
    latency_ms: 180,
  }),
  makeObservation({
    observed_at: '2026-07-17T09:55:00.000Z',
    location: 'SYNTHETIC_LOCATION-0000000000000060',
    health: 'degraded',
    latency_ms: 700,
  }),
]

describe('latestPerLocation', () => {
  it('keeps only the newest observation per distinct location, in first-seen order', () => {
    const rows = latestPerLocation(TWO_LOCATIONS)
    expect(rows).toHaveLength(2)
    expect(rows[0]).toEqual({
      location: 'SYNTHETIC_LOCATION-0000000000000060',
      status: 'up',
      latencyMs: 210,
      observedAt: '2026-07-17T10:05:00.000Z',
    })
    expect(rows[1]).toEqual({
      location: 'SYNTHETIC_LOCATION-0000000000000061',
      status: 'degraded',
      latencyMs: 900,
      observedAt: '2026-07-17T10:04:00.000Z',
    })
  })

  it('collapses a single-location series to exactly one row', () => {
    const rows = latestPerLocation(SINGLE_LOCATION)
    expect(rows).toHaveLength(1)
    expect(rows[0].latencyMs).toBe(180)
  })

  it('returns an empty array for an empty input, never throwing', () => {
    expect(latestPerLocation([])).toEqual([])
  })
})

function Harness({ signalKey }: { signalKey: string | undefined }) {
  const { state } = useProposalEvidence(signalKey)

  if (state.phase === 'loading') return <div role="status">Loading…</div>
  if (state.phase === 'error') return <p role="alert">{state.message}</p>

  return (
    <ul>
      {state.data.map((row) => (
        <li key={row.location}>
          {row.location} | {row.status} | {row.latencyMs ?? 'no-lat'}
        </li>
      ))}
    </ul>
  )
}

describe('useProposalEvidence', () => {
  it('resolves latest-per-location rows across 2 distinct locations', async () => {
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        expect(url.searchParams.get('signal_key')).toBe('http-check')
        expect(url.searchParams.get('limit')).not.toBeNull()
        return HttpResponse.json(TWO_LOCATIONS)
      }),
    )

    render(<Harness signalKey="http-check" />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(2)
  })

  it('resolves a single row when every observation shares one location', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json(SINGLE_LOCATION)))

    render(<Harness signalKey="http-check" />)

    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(1)
    expect(items[0]).toHaveTextContent('180')
  })

  it("surfaces a fetch failure as this hook's own error state, without throwing", async () => {
    server.use(
      http.get('/api/v1/history', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )

    render(<Harness signalKey="http-check" />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })

  it('short-circuits to an empty success result when there is no signal key, never fetching', async () => {
    let fetchCount = 0
    server.use(
      http.get('/api/v1/history', () => {
        fetchCount += 1
        return HttpResponse.json(TWO_LOCATIONS)
      }),
    )

    render(<Harness signalKey={undefined} />)

    const list = await screen.findByRole('list')
    expect(list.children).toHaveLength(0)
    expect(fetchCount).toBe(0)
  })
})
