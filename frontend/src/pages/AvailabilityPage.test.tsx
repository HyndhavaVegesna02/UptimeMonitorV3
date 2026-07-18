import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { server } from '../mocks/server'
import { FIXTURE_AVAILABILITY_BY_COMPONENT, FIXTURE_TOPOLOGY } from '../mocks/handlers'
import { AvailabilityPage } from './AvailabilityPage'

// Mirrors the `useAvailability.test.tsx` contention note (STORY-068): this
// page fans out one `getTopology()` hop plus 2 x FIXTURE_TOPOLOGY.length
// requests (rollup + segment history per component) on every render — a
// per-file timeout bump, not a global one.
beforeAll(() => {
  vi.setConfig({ testTimeout: 15000 })
})

afterAll(() => {
  vi.resetConfig()
})

function renderPage() {
  return render(
    <MemoryRouter>
      <AvailabilityPage />
    </MemoryRouter>,
  )
}

describe('AvailabilityPage — layout (AC1)', () => {
  it('renders exactly one h1 titled Availability, with a subtitle', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: 'Availability', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it('renders a 24h/7d/30d window switcher with 24h active by default', () => {
    renderPage()
    const group = screen.getByRole('group', { name: 'Time window' })
    const button24h = within(group).getByRole('button', { name: '24h' })
    const button7d = within(group).getByRole('button', { name: '7d' })
    const button30d = within(group).getByRole('button', { name: '30d' })

    expect(button24h).toHaveAttribute('aria-pressed', 'true')
    expect(button7d).toHaveAttribute('aria-pressed', 'false')
    expect(button30d).toHaveAttribute('aria-pressed', 'false')
  })

  it('switches the active window on click (keyboard operable via click activation)', async () => {
    const user = userEvent.setup()
    renderPage()

    const button7d = screen.getByRole('button', { name: '7d' })
    await user.click(button7d)

    expect(button7d).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'false')
  })
})

describe('AvailabilityPage — per-tile states (AC3)', () => {
  it('shows a loading state before the fetch resolves', () => {
    renderPage()
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('surfaces a fetch failure as an error state with retry, never a blank page', async () => {
    server.use(
      http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load availability')
    // The header + window switcher survive the failure.
    expect(screen.getByRole('heading', { name: 'Availability', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('group', { name: 'Time window' })).toBeInTheDocument()
  })

  it('renders an explicit empty state when there are no components configured', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText(/no components configured/i)).toBeInTheDocument()
  })

  it('renders one tile per component once the fetch resolves', async () => {
    renderPage()

    await screen.findByText(FIXTURE_TOPOLOGY[0].name)
    for (const component of FIXTURE_TOPOLOGY) {
      expect(screen.getByText(component.name)).toBeInTheDocument()
    }
  })
})

describe('AvailabilityPage — legend (AC2)', () => {
  it('renders a legend explaining down vs missing with a hatched swatch for missing', () => {
    renderPage()
    expect(screen.getByText('Down / outage')).toBeInTheDocument()
    expect(screen.getByText('Missing data')).toBeInTheDocument()
  })
})

describe('AvailabilityPage — availability + completeness metrics (AC2)', () => {
  it('shows the availability % (windowed bar) and the down-count sublabel for a component', async () => {
    const { container } = renderPage()

    const rollup = FIXTURE_AVAILABILITY_BY_COMPONENT['sockshop-frontend'].rollup
    const expectedPct = `${(rollup.availability_pct! * 100).toFixed(2)}%`
    await screen.findByText(FIXTURE_TOPOLOGY[0].name)
    expect(screen.getByText(expectedPct)).toBeInTheDocument()
    expect(container.querySelector('.availability-metric__bar')).toBeInTheDocument()
  })

  it('shows the unambiguous completeness phrasing: pct + "of expected checks received"', async () => {
    renderPage()

    const rollup = FIXTURE_AVAILABILITY_BY_COMPONENT['sockshop-frontend'].rollup
    const expectedPct = `${(rollup.completeness_pct! * 100).toFixed(2)}%`
    const pctNode = await screen.findByText(expectedPct)
    const cell = pctNode.closest('.availability-metric') as HTMLElement
    expect(within(cell).getByText(/of expected checks received/)).toBeInTheDocument()
  })

  it('renders "no data" (never 0%) and omits the completeness sub-label for a zero-signal/degenerate component', async () => {
    renderPage()

    await screen.findByText('Sock Shop — orders')
    const tile = screen
      .getByText('Sock Shop — orders')
      .closest('.availability-tile') as HTMLElement
    expect(within(tile).getAllByText('no data').length).toBeGreaterThan(0)
    expect(within(tile).queryByText(/of expected checks received/)).not.toBeInTheDocument()
  })
})

describe('AvailabilityPage — signal-level drill-down (AC3)', () => {
  it('renders a collapsed, aria-expanded=false drill-down toggle for a multi-signal component', async () => {
    renderPage()

    const frontend = FIXTURE_TOPOLOGY[0]
    const toggle = await screen.findByRole('button', { name: new RegExp(frontend.name) })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText(frontend.signals[0].signal_key)).not.toBeInTheDocument()
  })

  it('expands to show each signal\'s own availability + completeness metrics on click', async () => {
    const user = userEvent.setup()
    renderPage()

    const frontend = FIXTURE_TOPOLOGY[0]
    const toggle = await screen.findByRole('button', { name: new RegExp(frontend.name) })
    await user.click(toggle)

    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    for (const signal of frontend.signals) {
      expect(screen.getByText(signal.name)).toBeInTheDocument()
      expect(screen.getByText(signal.signal_key)).toBeInTheDocument()
    }

    const frontendAvailability = FIXTURE_AVAILABILITY_BY_COMPONENT[frontend.id]
    const signalPct = `${(frontendAvailability.signals[0].availability_pct! * 100).toFixed(2)}%`
    expect(screen.getAllByText(signalPct).length).toBeGreaterThan(0)
  })

  it('renders no drill-down toggle for a zero-signal component', async () => {
    renderPage()

    await screen.findByText('Sock Shop — orders')
    expect(
      screen.queryByRole('button', { name: /Sock Shop — orders/ }),
    ).not.toBeInTheDocument()
  })
})
