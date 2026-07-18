import { render, screen, within } from '@testing-library/react'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import { server } from '../mocks/server'
import {
  FIXTURE_AVAILABILITY_BY_COMPONENT,
  FIXTURE_COMPONENTS,
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_PROPOSALS,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import { DashboardPage } from './DashboardPage'

function renderPage() {
  return render(
    <MemoryRouter>
      <DashboardPage />
    </MemoryRouter>,
  )
}

describe('DashboardPage — layout (AC1)', () => {
  it('renders exactly one h1 titled Dashboard', () => {
    renderPage()
    expect(screen.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it('renders the bento grid with a hero tile, one tile per component, both action tiles, and a feed tile', async () => {
    const { container } = renderPage()

    await screen.findAllByText(FIXTURE_COMPONENTS[0].name)

    expect(container.querySelector('.dashboard-grid')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-grid__hero')).toBeInTheDocument()
    expect(container.querySelectorAll('.dashboard-grid__component')).toHaveLength(
      FIXTURE_COMPONENTS.length,
    )
    expect(container.querySelector('.dashboard-grid__action--approvals')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-grid__action--maintenance')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-grid__feed')).toBeInTheDocument()
  })
})

describe('DashboardPage — hero tile (AC2)', () => {
  it('shows the worst-of status as the KPI + badge, and an honest "N of M operational" subline', async () => {
    const { container } = renderPage()

    const hero = container.querySelector('.dashboard-grid__hero') as HTMLElement
    // FIXTURE_COMPONENTS: one operational, one degraded -> worst-of = degraded.
    await within(hero).findByText('1 of 2 components operational')
    expect(hero.querySelector('.dashboard-grid__hero-kpi')).toHaveTextContent('Degraded')
    expect(hero.querySelector('.status-badge--degraded')).toBeInTheDocument()
  })

  it('shows "Up" + "N of N operational" when every component resolves healthy', async () => {
    server.use(
      http.get('/api/v1/components', () =>
        HttpResponse.json([
          { id: 'a', name: 'A', status: 'operational' },
          { id: 'b', name: 'B', status: 'operational' },
        ]),
      ),
    )
    const { container } = renderPage()
    const hero = container.querySelector('.dashboard-grid__hero') as HTMLElement

    expect(await within(hero).findByText('2 of 2 components operational')).toBeInTheDocument()
  })
})

describe('DashboardPage — per-component tiles (AC2)', () => {
  it('renders name, status badge, uptime %, latency spark, last-observed, and a drill-through link', async () => {
    renderPage()

    const frontend = FIXTURE_TOPOLOGY[0]
    const link = await screen.findByRole('link', { name: new RegExp(FIXTURE_COMPONENTS[0].name) })
    expect(link).toHaveAttribute(
      'href',
      `/check-history?signal=${frontend.signals[0].signal_key}`,
    )

    const pct = FIXTURE_AVAILABILITY_BY_COMPONENT[frontend.id].rollup.availability_pct!
    expect(await within(link).findByText(`${(pct * 100).toFixed(2)}%`)).toBeInTheDocument()

    const latestLatency = FIXTURE_HISTORY_FRONTEND_HTTP[0].latency_ms
    expect(
      within(link).getByRole('img', { name: new RegExp(`latest ${latestLatency} ms`) }),
    ).toBeInTheDocument()
  })

  it('renders a non-interactive tile (no link) for a component with no topology signals', async () => {
    server.use(
      http.get('/api/v1/components', () =>
        HttpResponse.json([
          { id: 'sockshop-orders', name: 'Sock Shop — orders', status: 'operational' },
        ]),
      ),
    )
    renderPage()

    await screen.findByText('Sock Shop — orders')
    expect(screen.queryByRole('link', { name: /Sock Shop — orders/ })).not.toBeInTheDocument()
  })
})

describe('DashboardPage — action tiles (AC2)', () => {
  it('shows the pending-approvals count as a whole-tile link, accented when > 0', async () => {
    const { container } = renderPage()

    const tile = (await screen.findByRole('link', {
      name: /Pending approvals/,
    })) as HTMLElement
    expect(tile).toHaveAttribute('href', '/approvals')
    expect(within(tile).getByText(String(FIXTURE_PROPOSALS.length))).toBeInTheDocument()
    expect(container.querySelector('.dashboard-grid__action--active')).toBeInTheDocument()
  })

  it('renders neutral (no accent) at zero pending approvals', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))
    const { container } = renderPage()

    const tile = await screen.findByRole('link', { name: /Pending approvals/ })
    expect(within(tile).getByText('0')).toBeInTheDocument()
    expect(container.querySelector('.dashboard-grid__action--active')).not.toBeInTheDocument()
  })

  it('shows the active-or-upcoming maintenance count as a whole-tile link, accented when > 0', async () => {
    const future = new Date(Date.now() + 60 * 60 * 1000).toISOString()
    server.use(
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json([
          { id: 1, component_id: 'a', starts_at: future, ends_at: future, reason: null, title: null },
        ]),
      ),
    )
    const { container } = renderPage()

    const tile = (await screen.findByRole('link', { name: /Maintenance/ })) as HTMLElement
    expect(tile).toHaveAttribute('href', '/maintenance')
    expect(within(tile).getByText('1')).toBeInTheDocument()
    expect(
      container.querySelector('.dashboard-grid__action--maintenance.dashboard-grid__action--active'),
    ).toBeInTheDocument()
  })

  it('renders neutral (no accent) when every fixtured maintenance window is past (real clock)', async () => {
    const { container } = renderPage()

    await screen.findByRole('link', { name: /Maintenance/ })
    expect(
      container.querySelector('.dashboard-grid__action--maintenance.dashboard-grid__action--active'),
    ).not.toBeInTheDocument()
    expect(
      within(container.querySelector('.dashboard-grid__action--maintenance') as HTMLElement).getByText(
        '0',
      ),
    ).toBeInTheDocument()
  })
})

describe('DashboardPage — recent-checks feed tile (AC3)', () => {
  it('shows the most recent checks with RelativeTime + a short location label + status + latency, never a raw ISO/vendor id', async () => {
    const { container } = renderPage()

    const feed = (await screen.findByText('Recent checks')).closest(
      '.dashboard-grid__feed',
    ) as HTMLElement

    const newest = FIXTURE_HISTORY_FRONTEND_HTTP[0]
    expect(await within(feed).findByText(`${newest.latency_ms} ms`)).toBeInTheDocument()
    expect(within(feed).getAllByText('Location …0060').length).toBeGreaterThan(0)

    // No raw vendor location id or raw ISO timestamp ever appears as text.
    expect(container.textContent).not.toContain('SYNTHETIC_LOCATION')
    expect(container.textContent).not.toContain(newest.observed_at)
  })

  it('renders an explicit empty state when there is nothing to show', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json([])))
    renderPage()

    const feedHeading = await screen.findByText('Recent checks')
    const feed = feedHeading.closest('.dashboard-grid__feed') as HTMLElement
    expect(await within(feed).findByText(/no checks/i)).toBeInTheDocument()
  })
})

describe('DashboardPage — per-tile loading/error states (AC4)', () => {
  it('shows a loading skeleton in every tile before any fetch resolves', () => {
    renderPage()
    expect(screen.getAllByRole('status').length).toBeGreaterThan(0)
  })

  it('surfaces a components failure as the hero tile\'s own error state, without blanking the rest of the page', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )
    const { container } = renderPage()

    const hero = container.querySelector('.dashboard-grid__hero') as HTMLElement
    expect(await within(hero).findByRole('alert')).toHaveTextContent('Could not load system status')

    // The independently-fetched tiles still render their own real data.
    expect(await screen.findByText('Recent checks')).toBeInTheDocument()
    expect(await screen.findByRole('link', { name: /Pending approvals/ })).toBeInTheDocument()
  })

  it('surfaces a maintenance failure as that tile\'s own error state with retry, without blanking the rest of the page', async () => {
    server.use(
      http.get('/api/v1/maintenance', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )
    const { container } = renderPage()

    const maintenanceTile = container.querySelector(
      '.dashboard-grid__action--maintenance',
    ) as HTMLElement
    expect(await within(maintenanceTile).findByRole('alert')).toHaveTextContent(
      'Could not load maintenance',
    )

    // The hero + component tiles are unaffected.
    expect((await screen.findAllByText(FIXTURE_COMPONENTS[0].name)).length).toBeGreaterThan(0)
  })

  it('surfaces a recent-checks failure as the feed tile\'s own error state with retry', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage()

    const feedHeading = await screen.findByText('Recent checks')
    const feed = feedHeading.closest('.dashboard-grid__feed') as HTMLElement
    expect(await within(feed).findByRole('alert')).toHaveTextContent('Could not load recent checks')
  })
})
