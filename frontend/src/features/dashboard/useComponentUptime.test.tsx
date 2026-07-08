import { render, screen } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import {
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_TOPOLOGY,
} from '../../mocks/handlers'
import type { AvailabilityRange } from '../availability/windowRange'
import { buildUptimeSegments, useComponentUptime } from './useComponentUptime'

const RANGE: AvailabilityRange = {
  since: '2026-07-02T00:00:00.000Z',
  until: '2026-07-03T00:00:00.000Z',
}

/** Minimal harness rendering every phase, mirroring how `DashboardPage`
 * will drive this hook. */
function Harness({ topology = FIXTURE_TOPOLOGY }: { topology?: typeof FIXTURE_TOPOLOGY }) {
  const { state } = useComponentUptime(topology, RANGE)

  if (state.phase === 'loading') {
    return <div role="status">Loading…</div>
  }

  if (state.phase === 'error') {
    return <p role="alert">{state.message}</p>
  }

  return (
    <ul>
      {topology.map((component) => {
        const uptime = state.data[component.id]
        return (
          <li key={component.id}>
            {component.name}: pct={String(uptime?.pct)} segments={uptime?.segments.length ?? 0}
          </li>
        )
      })}
    </ul>
  )
}

describe('buildUptimeSegments', () => {
  it('reverses newest-first observations into oldest -> newest segments', () => {
    const segments = buildUptimeSegments(FIXTURE_HISTORY_FRONTEND_HTTP)

    expect(segments).toHaveLength(FIXTURE_HISTORY_FRONTEND_HTTP.length)
    // The API's LAST (oldest) entry becomes the FIRST segment.
    const oldest = FIXTURE_HISTORY_FRONTEND_HTTP[FIXTURE_HISTORY_FRONTEND_HTTP.length - 1]
    expect(segments[0].title).toContain(oldest.location)
    const newest = FIXTURE_HISTORY_FRONTEND_HTTP[0]
    expect(segments[segments.length - 1].title).toContain(newest.location)
  })

  it('maps each observation health onto its StatusBadge health status', () => {
    const segments = buildUptimeSegments(FIXTURE_HISTORY_FRONTEND_HTTP)
    // health values present in the fixture: up, degraded, down, up
    expect(segments.map((s) => s.status).sort()).toEqual(['degraded', 'down', 'up', 'up'].sort())
  })

  it('caps at MAX_UPTIME_SEGMENTS, keeping the MOST RECENT observations', () => {
    const many = Array.from({ length: 45 }, (_, i) => ({
      signal_key: 'sig',
      observed_at: `2026-07-0${(i % 9) + 1}T00:00:00Z`,
      health: 'up',
      location: `loc-${i}`,
      latency_ms: 100,
    }))
    const segments = buildUptimeSegments(many)
    expect(segments).toHaveLength(30)
    // The 30 most recent (indices 0..29 of the newest-first input) survive,
    // reversed so index 29 (2nd-most-recent... ) ends up first; the very
    // newest (index 0) ends up last.
    expect(segments[segments.length - 1].title).toContain('loc-0')
  })

  it('produces no segments for an empty history — never a fabricated bar', () => {
    expect(buildUptimeSegments([])).toEqual([])
  })
})

describe('useComponentUptime', () => {
  it('combines each component real availability_pct with its first-signal sparkline', async () => {
    render(<Harness />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const frontend = FIXTURE_TOPOLOGY[0]
    const frontendPct = FIXTURE_AVAILABILITY_BY_COMPONENT[frontend.id].rollup.availability_pct
    expect(
      await screen.findByText(
        `${frontend.name}: pct=${frontendPct} segments=${FIXTURE_HISTORY_FRONTEND_HTTP.length}`,
      ),
    ).toBeInTheDocument()
  })

  it('renders an honest null pct + empty segments for a zero-signal component (never fabricated)', async () => {
    render(<Harness />)

    const orders = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-orders')!
    expect(await screen.findByText(`${orders.name}: pct=null segments=0`)).toBeInTheDocument()
  })

  it('renders empty segments (no fabricated data) when the signal has no history for the window', async () => {
    render(<Harness />)

    const catalogue = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-catalogue')!
    const pct = FIXTURE_AVAILABILITY_BY_COMPONENT[catalogue.id].rollup.availability_pct
    expect(
      await screen.findByText(`${catalogue.name}: pct=${pct} segments=0`),
    ).toBeInTheDocument()
  })

  it('isolates ONE component availability failure — every other row still gets real data', async () => {
    const failingId = FIXTURE_TOPOLOGY[1].id // sockshop-catalogue
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ params }) => {
        if (params.componentId === failingId) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[params.componentId as string]
        return HttpResponse.json(dto)
      }),
    )

    render(<Harness />)

    const frontend = FIXTURE_TOPOLOGY[0]
    const frontendPct = FIXTURE_AVAILABILITY_BY_COMPONENT[frontend.id].rollup.availability_pct
    // The failing component degrades to null/no-segments...
    expect(
      await screen.findByText(`${FIXTURE_TOPOLOGY[1].name}: pct=null segments=0`),
    ).toBeInTheDocument()
    // ...while an UNRELATED component's real data survives — the hook's
    // own state never reaches 'error' over one row's failure.
    expect(
      screen.getByText(
        `${frontend.name}: pct=${frontendPct} segments=${FIXTURE_HISTORY_FRONTEND_HTTP.length}`,
      ),
    ).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  })
})
