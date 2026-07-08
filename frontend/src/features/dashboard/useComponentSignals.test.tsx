import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_HISTORY_FRONTEND_TLS,
  FIXTURE_TOPOLOGY,
} from '../../mocks/handlers'
import type { ObservationDTO, TopologySignalDTO } from '../../api/types'
import type { AvailabilityRange } from '../availability/windowRange'
import { buildSignalRows, useComponentSignals } from './useComponentSignals'

const RANGE: AvailabilityRange = {
  since: '2026-07-02T00:00:00.000Z',
  until: '2026-07-03T00:00:00.000Z',
}

const FRONTEND_SIGNALS = FIXTURE_TOPOLOGY[0].signals

function Harness({ signals }: { signals: TopologySignalDTO[] }) {
  const { state } = useComponentSignals(signals, RANGE)

  if (state.phase === 'loading') return <div role="status">Loading…</div>
  if (state.phase === 'error') return <p role="alert">{state.message}</p>

  return (
    <ul>
      {state.data.map((row) => (
        <li key={row.key}>
          {row.label} | {row.location ?? 'no-loc'} | {row.status} |{' '}
          {row.latencyMs ?? 'no-lat'} | {row.lastObserved ?? 'no-last'}
        </li>
      ))}
    </ul>
  )
}

describe('buildSignalRows', () => {
  it('keeps the latest observation per (signal, location) pair', () => {
    const history: Record<string, ObservationDTO[]> = {
      'frontend-http': FIXTURE_HISTORY_FRONTEND_HTTP,
    }
    const signals = [FRONTEND_SIGNALS[0]]
    const rows = buildSignalRows(signals, history)

    // FIXTURE_HISTORY_FRONTEND_HTTP has 3 distinct locations (…60 appears
    // twice) -> 3 rows, and location …60's row is the NEWEST …60 observation.
    expect(rows).toHaveLength(3)
    const loc60 = rows.find((r) => r.location === 'SYNTHETIC_LOCATION-0000000000000060')
    expect(loc60).toBeDefined()
    // Newest …60 row is the health='up', 571ms, 13:29:17 one (not the down/null older one).
    expect(loc60?.status).toBe('up')
    expect(loc60?.latencyMs).toBe(571)
    expect(loc60?.lastObserved).toBe('2026-07-03T13:29:17.931000Z')
  })

  it('emits one honest missing-data row for a signal with no observations', () => {
    const rows = buildSignalRows([FRONTEND_SIGNALS[0]], { 'frontend-http': [] })
    expect(rows).toHaveLength(1)
    expect(rows[0].status).toBe('missing')
    expect(rows[0].location).toBeNull()
    expect(rows[0].latencyMs).toBeNull()
    expect(rows[0].lastObserved).toBeNull()
    expect(rows[0].label).toBe(FRONTEND_SIGNALS[0].name)
  })

  it('carries the topology signal name as the row label', () => {
    const rows = buildSignalRows([FRONTEND_SIGNALS[1]], {
      'frontend-tls': FIXTURE_HISTORY_FRONTEND_TLS,
    })
    expect(rows.every((r) => r.label === FRONTEND_SIGNALS[1].name)).toBe(true)
  })
})

describe('useComponentSignals', () => {
  it('fetches each signal history and flattens to latest-per-location rows', async () => {
    render(<Harness signals={FRONTEND_SIGNALS} />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    // frontend-http -> 3 location rows; frontend-tls -> 1 location row (…63).
    const items = await screen.findAllByRole('listitem')
    expect(items).toHaveLength(4)
    expect(
      screen.getByText(/Frontend HTTP check \| SYNTHETIC_LOCATION-0000000000000060 \| up/),
    ).toBeInTheDocument()
  })

  it('surfaces a per-drilldown error without throwing', async () => {
    server.use(
      http.get('/api/v1/history', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    render(<Harness signals={FRONTEND_SIGNALS} />)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
