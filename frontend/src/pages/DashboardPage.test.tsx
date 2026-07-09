import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_COMPONENTS, FIXTURE_COMPONENTS_ALL_STATUSES } from '../mocks/handlers'
import { DashboardPage } from './DashboardPage'

/** Scopes a summary-card lookup to the summary row — several status LABELS
 * (e.g. "Degraded") are shared with the per-row `StatusBadge` text below,
 * so an unscoped `getByText` would find both. */
function cardFor(label: string): HTMLElement {
  const summary = document.querySelector('.dashboard-page__summary') as HTMLElement
  return within(summary).getByText(label).closest('.summary-card') as HTMLElement
}

describe('DashboardPage', () => {
  it('shows a loading state, then a table with one row per component (AC1, AC2)', async () => {
    render(<DashboardPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    // Semantic column headers (AC1: `<th scope="col">` via the shared `Table` primitive).
    expect(
      screen.getByRole('columnheader', { name: 'Component' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('columnheader', { name: 'Uptime' })).toBeInTheDocument()
    expect(
      screen.getByRole('columnheader', { name: 'Status' }),
    ).toBeInTheDocument()

    expect(screen.getByText(FIXTURE_COMPONENTS[0].name)).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[1].name)).toBeInTheDocument()
    // operational -> "Up", degraded -> "Degraded" (src/api/statusMapping.ts)
    // — scoped to the table since the summary-card row above also has a
    // "Degraded" label.
    expect(within(table).getByText('Up')).toBeInTheDocument()
    expect(within(table).getByText('Degraded')).toBeInTheDocument()

    // Exactly one data row per fixture component (no row expanded).
    expect(screen.getAllByRole('row')).toHaveLength(FIXTURE_COMPONENTS.length + 1)
  })

  it('renders a SummaryCard row derived from real component counts (AC1)', async () => {
    render(<DashboardPage />)
    await screen.findByRole('table')

    // FIXTURE_COMPONENTS: 1 operational + 1 degraded, no partial/down/unknown.
    expect(within(cardFor('Components')).getByText('2')).toBeInTheDocument()
    expect(within(cardFor('Operational')).getByText('1')).toBeInTheDocument()
    expect(within(cardFor('Degraded')).getByText('1')).toBeInTheDocument()
    expect(within(cardFor('Partial outage')).getByText('0')).toBeInTheDocument()
    expect(within(cardFor('Down')).getByText('0')).toBeInTheDocument()
    expect(screen.queryByText('Unknown')).not.toBeInTheDocument()
  })

  it('renders the empty state when the backend returns no components (AC2)', async () => {
    server.use(http.get('/api/v1/components', () => HttpResponse.json([])))

    render(<DashboardPage />)

    expect(
      await screen.findByText('No components configured'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows an error state on failure, then recovers via retry (AC2)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/components', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_COMPONENTS)
      }),
    )

    render(<DashboardPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not load components',
    )

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(
      await screen.findByText(FIXTURE_COMPONENTS[0].name),
    ).toBeInTheDocument()
    expect(callCount).toBe(2)
  })

  it('maps each backend status onto the correct accessible badge label, including unknown (AC3)', async () => {
    server.use(
      http.get('/api/v1/components', () =>
        HttpResponse.json(FIXTURE_COMPONENTS_ALL_STATUSES),
      ),
    )

    render(<DashboardPage />)

    await screen.findByRole('table')

    const dataRows = screen.getAllByRole('row').slice(1) // drop the header row

    const expectations: Array<[string, string]> = [
      ['Operational Component', 'Up'],
      ['Degraded Component', 'Degraded'],
      ['Partial Outage Component', 'Partial outage'],
      ['Major Outage Component', 'Down'],
      ['Mystery Component', 'Unknown'],
    ]

    for (const [name, label] of expectations) {
      const row = dataRows.find((candidate) =>
        within(candidate).queryByText(name),
      )
      expect(row).toBeDefined()
      expect(within(row as HTMLElement).getByText(label)).toBeInTheDocument()
    }
  })

  it('binds the per-row uptime % and sparkline to real availability/history, omitting fabricated segments where none exist (AC3)', async () => {
    render(<DashboardPage />)
    await screen.findByRole('table')

    // sockshop-frontend: real availability_pct (0.995) + a real 4-observation
    // sparkline built from FIXTURE_HISTORY_FRONTEND_HTTP.
    expect(await screen.findByText('99.50%')).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: /Sock Shop — frontend uptime/ }),
    ).toBeInTheDocument()

    // sockshop-catalogue: real availability_pct (0.982), but its primary
    // signal (catalogue-http) has no fixtured history -> the shared
    // `UptimeBar`'s own explicit "no data" state, never a fabricated bar.
    expect(await screen.findByText('98.20%')).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: 'Sock Shop — catalogue uptime: no data' }),
    ).toBeInTheDocument()
  })

  it('expands a component row to its real signal drill-down: location/status/latency/last-observed (AC2)', async () => {
    const user = userEvent.setup()
    render(<DashboardPage />)
    await screen.findByRole('table')

    const toggle = await screen.findByRole('button', { name: FIXTURE_COMPONENTS[0].name })
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'true')

    expect(await screen.findByText('Signals feeding this component')).toBeInTheDocument()
    // frontend-http -> 3 distinct-location rows; frontend-tls -> 1.
    expect(screen.getAllByText('Frontend HTTP check')).toHaveLength(3)
    expect(screen.getAllByText('Frontend TLS check')).toHaveLength(1)
    expect(screen.getByText('SYNTHETIC_LOCATION-0000000000000060')).toBeInTheDocument()
    expect(screen.getByText('571 ms')).toBeInTheDocument()

    await user.click(toggle)
    expect(toggle).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByText('Signals feeding this component')).not.toBeInTheDocument()
  })

  it('is keyboard-operable: focus + Enter toggles the expand affordance (AC2)', async () => {
    const user = userEvent.setup()
    render(<DashboardPage />)
    await screen.findByRole('table')

    const toggle = await screen.findByRole('button', { name: FIXTURE_COMPONENTS[0].name })
    toggle.focus()
    expect(toggle).toHaveAttribute('aria-expanded', 'false')

    await user.keyboard('{Enter}')
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
  })

  it('degrades gracefully: a topology failure still renders the components table with no expand affordance (AC2)', async () => {
    server.use(
      http.get('/api/v1/topology', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    render(<DashboardPage />)
    await screen.findByRole('table')

    expect(screen.getByText(FIXTURE_COMPONENTS[0].name)).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: FIXTURE_COMPONENTS[0].name }),
    ).not.toBeInTheDocument()
  })

  it('degrades gracefully: a signal drill-down failure is scoped to the expanded row only (AC2)', async () => {
    const user = userEvent.setup()
    server.use(
      http.get('/api/v1/history', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    render(<DashboardPage />)
    await screen.findByRole('table')

    const toggle = await screen.findByRole('button', { name: FIXTURE_COMPONENTS[0].name })
    await user.click(toggle)

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load signals')
    // The primary table is untouched by the drill-down's own failure.
    expect(screen.getByText(FIXTURE_COMPONENTS[0].name)).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[1].name)).toBeInTheDocument()
  })
})

describe('DashboardPage — maintenance indicator (STORY-046)', () => {
  // Fixed instant so active/upcoming/past/boundary windows are deterministic
  // (2026-06-25 working-agreement: non-aligned-boundary tests pin `now`).
  const NOW = new Date('2026-07-07T10:30:00Z')

  beforeEach(() => {
    // `vi.setSystemTime` alone (without `vi.useFakeTimers()`) mocks `Date`
    // for the deterministic windowState assertions below WITHOUT freezing
    // real timers — MSW's fetch handling relies on real timers, so faking
    // them would hang every awaited request (mirrors MaintenancePage.test.tsx).
    vi.setSystemTime(NOW)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const MAINTENANCE_COMPONENTS = [
    { id: 'comp-active', name: 'Active Window Component', status: 'operational' },
    { id: 'comp-upcoming', name: 'Upcoming Window Component', status: 'operational' },
    { id: 'comp-past', name: 'Past Window Component', status: 'operational' },
    { id: 'comp-none', name: 'No Window Component', status: 'operational' },
    { id: 'comp-boundary-start', name: 'Boundary Start Component', status: 'operational' },
    { id: 'comp-boundary-end', name: 'Boundary End Component', status: 'operational' },
  ]

  // Real wire shape (id/component_id/starts_at/ends_at/reason) per
  // `MaintenanceWindowDTO`.
  const ACTIVE_WINDOW = {
    id: 101,
    component_id: 'comp-active',
    starts_at: '2026-07-07T10:00:00Z',
    ends_at: '2026-07-07T11:00:00Z',
    reason: null,
  }
  const UPCOMING_WINDOW = {
    id: 102,
    component_id: 'comp-upcoming',
    starts_at: '2026-07-08T09:00:00Z',
    ends_at: '2026-07-08T10:00:00Z',
    reason: null,
  }
  const PAST_WINDOW = {
    id: 103,
    component_id: 'comp-past',
    starts_at: '2026-07-06T09:00:00Z',
    ends_at: '2026-07-06T10:00:00Z',
    reason: null,
  }
  // Half-open boundary (`starts_at <= now < ends_at`): AT starts_at, ACTIVE.
  const BOUNDARY_START_WINDOW = {
    id: 104,
    component_id: 'comp-boundary-start',
    starts_at: '2026-07-07T10:30:00Z', // === NOW
    ends_at: '2026-07-07T11:30:00Z',
    reason: null,
  }
  // AT ends_at, no longer active (past) — the other half of the boundary.
  const BOUNDARY_END_WINDOW = {
    id: 105,
    component_id: 'comp-boundary-end',
    starts_at: '2026-07-07T09:30:00Z',
    ends_at: '2026-07-07T10:30:00Z', // === NOW
    reason: null,
  }

  function rowFor(name: string): HTMLElement {
    return screen.getByText(name).closest('tr') as HTMLElement
  }

  it('marks only components with an ACTIVE window, including exact half-open boundaries (AC4)', async () => {
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json(MAINTENANCE_COMPONENTS)),
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json([
          ACTIVE_WINDOW,
          UPCOMING_WINDOW,
          PAST_WINDOW,
          BOUNDARY_START_WINDOW,
          BOUNDARY_END_WINDOW,
        ]),
      ),
    )

    render(<DashboardPage />)
    await screen.findByRole('table')

    // Active + the starts_at boundary instant ARE marked.
    expect(
      within(rowFor('Active Window Component')).getByText('Under maintenance'),
    ).toBeInTheDocument()
    expect(
      within(rowFor('Boundary Start Component')).getByText('Under maintenance'),
    ).toBeInTheDocument()

    // Upcoming, past, no-window, and the ends_at boundary instant are NOT.
    expect(
      within(rowFor('Upcoming Window Component')).queryByText('Under maintenance'),
    ).not.toBeInTheDocument()
    expect(
      within(rowFor('Past Window Component')).queryByText('Under maintenance'),
    ).not.toBeInTheDocument()
    expect(
      within(rowFor('No Window Component')).queryByText('Under maintenance'),
    ).not.toBeInTheDocument()
    expect(
      within(rowFor('Boundary End Component')).queryByText('Under maintenance'),
    ).not.toBeInTheDocument()
  })

  it('coexists with the health badge — a degraded component under active maintenance shows BOTH, non-color-only (AC4)', async () => {
    const DEGRADED_ACTIVE = {
      id: 'comp-degraded-active',
      name: 'Degraded Under Maintenance',
      status: 'degraded',
    }
    server.use(
      http.get('/api/v1/components', () => HttpResponse.json([DEGRADED_ACTIVE])),
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json([{ ...ACTIVE_WINDOW, component_id: DEGRADED_ACTIVE.id }]),
      ),
    )

    render(<DashboardPage />)
    await screen.findByRole('table')

    const row = rowFor(DEGRADED_ACTIVE.name)
    // Health status is preserved — the overlay never hides/replaces it.
    expect(within(row).getByText('Degraded')).toBeInTheDocument()
    // The maintenance indicator carries an accessible TEXT label of its
    // own — never a color-only cue.
    expect(within(row).getByText('Under maintenance')).toBeInTheDocument()
  })

  it('degrades gracefully: a /api/v1/maintenance failure still renders the components table, with no markers', async () => {
    server.use(
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    render(<DashboardPage />)

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[0].name)).toBeInTheDocument()
    expect(screen.queryByText('Under maintenance')).not.toBeInTheDocument()
  })
})
