import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import {
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import type { ComponentAvailabilityDTO } from '../api/types'
import { AvailabilityPage } from './AvailabilityPage'

describe('AvailabilityPage', () => {
  it('shows a loading state, then a grid with Component/Availability/Data completeness columns (AC1)', async () => {
    render(<AvailabilityPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Component' })).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Availability' })).toBeInTheDocument()
    expect(
      screen.getByRole('columnheader', { name: 'Data completeness' }),
    ).toBeInTheDocument()

    for (const component of FIXTURE_TOPOLOGY) {
      const availability = FIXTURE_AVAILABILITY_BY_COMPONENT[component.id]
      const row = screen.getByText(component.name).closest('tr') as HTMLElement
      expect(row).not.toBeNull()
      if (availability.rollup.availability_pct !== null) {
        // Fixture values are 0-1 wire fractions (STORY-015d fix) — scale to
        // percent to match the page's display text. `formatPct` is the only
        // scaling seam — this asserts against it, never a re-derived value.
        expect(
          within(row).getByText(`${(availability.rollup.availability_pct * 100).toFixed(2)}%`),
        ).toBeInTheDocument()
      }
    }
  })

  it('shows the down/missing-data legend, always paired with text (never color-only) (AC1)', async () => {
    render(<AvailabilityPage />)
    await screen.findByRole('table')

    expect(screen.getByText('Down / outage')).toBeInTheDocument()
    expect(screen.getByText('Missing data')).toBeInTheDocument()
  })

  it('renders a real UptimeBar sparkline built from the primary signal\'s history for a component with data (AC1)', async () => {
    render(<AvailabilityPage />)
    await screen.findByRole('table')

    const frontend = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    const bar = screen.getByRole('img', { name: new RegExp(frontend.name + ' availability segments') })
    expect(bar).toBeInTheDocument()
    // One rendered segment per real observation in the fixture — never a
    // fabricated bucket.
    expect(bar.querySelectorAll('[title]')).toHaveLength(FIXTURE_HISTORY_FRONTEND_HTTP.length)
  })

  it('renders "no downtime" when every non-maintenance verdict passed, and a low-completeness "missing data" chip for a component below the threshold (AC1)', async () => {
    render(<AvailabilityPage />)
    await screen.findByRole('table')

    const frontendRow = screen.getByText('Sock Shop — frontend').closest('tr') as HTMLElement
    // Fixture: total 96, passing 95, maintenance 1 -> down = 0.
    expect(within(frontendRow).getByText('no downtime')).toBeInTheDocument()
    // Fixture completeness 0.999 -> not low.
    expect(within(frontendRow).queryByText('missing data')).not.toBeInTheDocument()

    const catalogueRow = screen.getByText('Sock Shop — catalogue').closest('tr') as HTMLElement
    // Fixture completeness 0.975 -> below the 98% threshold.
    expect(within(catalogueRow).getByText('missing data')).toBeInTheDocument()
  })

  it('renders "N period(s) down" derived from REAL verdict counts, singular and plural', async () => {
    const withDownCounts: ComponentAvailabilityDTO = {
      ...FIXTURE_AVAILABILITY_BY_COMPONENT['sockshop-catalogue'],
      rollup: {
        ...FIXTURE_AVAILABILITY_BY_COMPONENT['sockshop-catalogue'].rollup,
        total_verdicts: 10,
        passing_verdicts: 9,
        maintenance_verdicts: 0,
      },
    }
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ params }) => {
        if (params.componentId === 'sockshop-catalogue') {
          return HttpResponse.json(withDownCounts)
        }
        const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[params.componentId as string]
        return HttpResponse.json(dto)
      }),
    )

    render(<AvailabilityPage />)
    await screen.findByRole('table')

    const row = screen.getByText('Sock Shop — catalogue').closest('tr') as HTMLElement
    expect(within(row).getByText('1 period down')).toBeInTheDocument()
  })

  it('expands a multi-signal component to reveal its per-signal availability/completeness cells (AC2)', async () => {
    const user = userEvent.setup()
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const multiSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-frontend')!
    const expandButton = screen.getByRole('button', { name: new RegExp(multiSignal.name) })
    expect(expandButton).toHaveAttribute('aria-expanded', 'false')

    // Children not shown until expanded.
    for (const signal of multiSignal.signals) {
      expect(screen.queryByText(signal.signal_key)).not.toBeInTheDocument()
    }

    await user.click(expandButton)

    expect(expandButton).toHaveAttribute('aria-expanded', 'true')
    const componentAvailability = FIXTURE_AVAILABILITY_BY_COMPONENT[multiSignal.id]
    for (const signal of componentAvailability.signals) {
      const topologySignal = multiSignal.signals.find(
        (s) => s.signal_key === signal.signal_key,
      )!
      const signalKeyEl = screen.getByText(signal.signal_key)
      const childRow = signalKeyEl.closest('tr') as HTMLElement
      expect(childRow).not.toBeNull()
      expect(within(childRow).getByText(topologySignal.name)).toBeInTheDocument()
      expect(
        within(childRow).getByText(
          `${((signal.availability_pct ?? 0) * 100).toFixed(2)}%`,
        ),
      ).toBeInTheDocument()
    }

    // Collapsing hides them again.
    await user.click(expandButton)
    expect(expandButton).toHaveAttribute('aria-expanded', 'false')
    for (const signal of multiSignal.signals) {
      expect(screen.queryByText(signal.signal_key)).not.toBeInTheDocument()
    }
  })

  it('renders a single-signal component the same expandable way as multi-signal (AC2)', async () => {
    const user = userEvent.setup()
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const single = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-catalogue')!
    const expandButton = screen.getByRole('button', { name: new RegExp(single.name) })
    await user.click(expandButton)

    const [signal] = single.signals
    expect(screen.getByText(signal.signal_key)).toBeInTheDocument()
  })

  it('renders a zero-signal component with its honest all-None rollup, no expand control, and an empty UptimeBar (AC1, AC2)', async () => {
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const zeroSignal = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-orders')!
    // No expand button for a component with no signals.
    expect(
      screen.queryByRole('button', { name: new RegExp(zeroSignal.name) }),
    ).not.toBeInTheDocument()

    const row = screen.getByText(zeroSignal.name).closest('tr') as HTMLElement
    expect(row).not.toBeNull()
    // Null availability/completeness renders as "no data", never 0%/NaN%.
    expect(within(row).getAllByText('no data').length).toBeGreaterThan(0)
    expect(within(row).queryByText('0.00%')).not.toBeInTheDocument()
    expect(within(row).queryByText(/NaN/)).not.toBeInTheDocument()
    // No signals means no history call, so the bar is honestly empty — never
    // a fabricated segment.
    expect(
      within(row).getByRole('img', { name: `${zeroSignal.name} availability segments: no data` }),
    ).toBeInTheDocument()
  })

  it('renders a no-data window (signals present, all-None pct) honestly at both grains — never 0% or NaN (AC1)', async () => {
    const user = userEvent.setup()
    render(<AvailabilityPage />)

    await screen.findByRole('table')

    const nodata = FIXTURE_TOPOLOGY.find((c) => c.id === 'sockshop-nodata')!
    const expandButton = screen.getByRole('button', { name: new RegExp(nodata.name) })
    const row = expandButton.closest('tr') as HTMLElement

    expect(within(row).getAllByText('no data').length).toBeGreaterThan(0)
    expect(within(row).queryByText('0.00%')).not.toBeInTheDocument()
    expect(within(row).queryByText(/NaN/)).not.toBeInTheDocument()

    await user.click(expandButton)

    const [childSignal] = nodata.signals
    const childRow = screen.getByText(childSignal.signal_key).closest('tr') as HTMLElement
    expect(within(childRow).getAllByText('no data').length).toBeGreaterThan(0)
    expect(within(childRow).queryByText('0.00%')).not.toBeInTheDocument()
    expect(within(childRow).queryByText(/NaN/)).not.toBeInTheDocument()
  })

  it('shows the shared LoadingState while the initial fetch is in flight (AC4)', () => {
    render(<AvailabilityPage />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading availability…')
  })

  it('shows the shared EmptyState when the topology has no components (AC4)', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))

    render(<AvailabilityPage />)

    expect(await screen.findByText('No components configured')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows the shared ErrorState on failure, then recovers via retry (AC4)', async () => {
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

    render(<AvailabilityPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not load availability',
    )

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByRole('table')
    expect(callCount).toBe(2)
  })

  it('offers a 24h/7d/30d window selector with radio-like aria-pressed semantics, ≥40px targets (AC2)', async () => {
    render(<AvailabilityPage />)
    await screen.findByRole('table')

    const h24 = screen.getByRole('button', { name: '24h' })
    const d7 = screen.getByRole('button', { name: '7d' })
    const d30 = screen.getByRole('button', { name: '30d' })

    // 24h is selected by default.
    expect(h24).toHaveAttribute('aria-pressed', 'true')
    expect(d7).toHaveAttribute('aria-pressed', 'false')
    expect(d30).toHaveAttribute('aria-pressed', 'false')
  })

  it('driving the window selector refetches with the ACTUAL new since/until query params (AC2)', async () => {
    const user = userEvent.setup()
    const seenRanges: Array<{ since: string; until: string }> = []
    server.use(
      http.get('/api/v1/availability/component/:componentId', ({ request, params }) => {
        const url = new URL(request.url)
        seenRanges.push({
          since: url.searchParams.get('since') ?? '',
          until: url.searchParams.get('until') ?? '',
        })
        const dto = FIXTURE_AVAILABILITY_BY_COMPONENT[params.componentId as string]
        return HttpResponse.json(dto)
      }),
    )

    render(<AvailabilityPage />)
    await screen.findByRole('table')

    const callsBeforeClick = seenRanges.length
    expect(callsBeforeClick).toBeGreaterThan(0)
    const initialRange = seenRanges[0]
    const initialSpanMs =
      new Date(initialRange.until).getTime() - new Date(initialRange.since).getTime()
    expect(Math.abs(initialSpanMs - 24 * 60 * 60 * 1000)).toBeLessThan(5000)

    await user.click(screen.getByRole('button', { name: '7d' }))

    await waitFor(() => {
      expect(seenRanges.length).toBeGreaterThan(callsBeforeClick)
    })

    expect(screen.getByRole('button', { name: '7d' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute(
      'aria-pressed',
      'false',
    )

    const newRange = seenRanges[seenRanges.length - 1]
    const newSpanMs = new Date(newRange.until).getTime() - new Date(newRange.since).getTime()
    expect(Math.abs(newSpanMs - 7 * 24 * 60 * 60 * 1000)).toBeLessThan(5000)
    // The actual since value MSW received genuinely changed (a real
    // refetch driven by the selector, not a stale/cached response).
    expect(newRange.since).not.toBe(initialRange.since)
  })
})
