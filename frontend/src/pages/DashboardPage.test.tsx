import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_COMPONENTS, FIXTURE_COMPONENTS_ALL_STATUSES } from '../mocks/handlers'
import { DashboardPage } from './DashboardPage'

describe('DashboardPage', () => {
  it('shows a loading state, then a table with one row per component (AC1, AC2)', async () => {
    render(<DashboardPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    // Semantic column headers (AC1: `<th scope="col">`).
    expect(
      screen.getByRole('columnheader', { name: 'Component' }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('columnheader', { name: 'Status' }),
    ).toBeInTheDocument()

    expect(screen.getByText(FIXTURE_COMPONENTS[0].name)).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_COMPONENTS[1].name)).toBeInTheDocument()
    // operational -> "Up", degraded -> "Degraded" (src/api/statusMapping.ts)
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Degraded')).toBeInTheDocument()

    // Exactly one data row per fixture component.
    expect(screen.getAllByRole('row')).toHaveLength(FIXTURE_COMPONENTS.length + 1)
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
})

describe('DashboardPage — sample mode toggle (STORY-049)', () => {
  it('renders the switch off by default, reflecting the GET, with no warning (AC1)', async () => {
    render(<DashboardPage />)
    await screen.findByRole('table')

    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')
    expect(
      screen.queryByText(/sample mode — signals recorded as down/i),
    ).not.toBeInTheDocument()
  })

  it('renders the switch on and the warning when the flag is already on (AC1, AC3)', async () => {
    server.use(http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))

    render(<DashboardPage />)

    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    expect(
      await screen.findByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()
  })

  it('does not render the switch until the initial GET resolves (loading case)', async () => {
    let resolveGet: (() => void) | undefined
    server.use(
      http.get('/api/v1/sample-mode', async () => {
        await new Promise<void>((resolve) => {
          resolveGet = resolve
        })
        return HttpResponse.json({ enabled: false })
      }),
    )

    render(<DashboardPage />)

    expect(screen.queryByRole('switch')).not.toBeInTheDocument()

    await waitFor(() => expect(resolveGet).toBeDefined())
    resolveGet?.()

    expect(await screen.findByRole('switch', { name: 'Sample mode' })).toBeInTheDocument()
  })

  it('toggling on PUTs { enabled: true } and shows the warning on success (AC2, AC3)', async () => {
    const user = userEvent.setup()
    let receivedBody: unknown
    server.use(
      http.put('/api/v1/sample-mode', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json({ enabled: true })
      }),
    )

    render(<DashboardPage />)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    await user.click(toggle)

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'))
    expect(receivedBody).toEqual({ enabled: true })
    expect(
      await screen.findByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()
  })

  it('toggling off PUTs { enabled: false } and the warning disappears (AC2, AC3)', async () => {
    const user = userEvent.setup()
    let receivedBody: unknown
    server.use(
      http.get('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })),
      http.put('/api/v1/sample-mode', async ({ request }) => {
        receivedBody = await request.json()
        return HttpResponse.json({ enabled: false })
      }),
    )

    render(<DashboardPage />)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    expect(
      await screen.findByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()

    await user.click(toggle)

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'false'))
    expect(receivedBody).toEqual({ enabled: false })
    expect(
      screen.queryByText(/sample mode — signals recorded as down/i),
    ).not.toBeInTheDocument()
  })

  it('on a failed PUT, shows an inline error and leaves aria-checked unchanged (AC2)', async () => {
    const user = userEvent.setup()
    server.use(
      http.put('/api/v1/sample-mode', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    render(<DashboardPage />)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    expect(toggle).toHaveAttribute('aria-checked', 'false')

    await user.click(toggle)

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(toggle).toHaveAttribute('aria-checked', 'false')
  })

  it('disables the switch while the PUT is in flight, re-enabling it once settled (AC2)', async () => {
    const user = userEvent.setup()
    let resolvePut: (() => void) | undefined
    server.use(
      http.put('/api/v1/sample-mode', async () => {
        await new Promise<void>((resolve) => {
          resolvePut = resolve
        })
        return HttpResponse.json({ enabled: true })
      }),
    )

    render(<DashboardPage />)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })

    await user.click(toggle)

    await waitFor(() => expect(toggle).toBeDisabled())

    resolvePut?.()

    await waitFor(() => expect(toggle).not.toBeDisabled())
    expect(toggle).toHaveAttribute('aria-checked', 'true')
  })

  it('is keyboard-operable: Enter on the focused switch toggles it (AC1)', async () => {
    const user = userEvent.setup()
    server.use(http.put('/api/v1/sample-mode', () => HttpResponse.json({ enabled: true })))

    render(<DashboardPage />)
    const toggle = await screen.findByRole('switch', { name: 'Sample mode' })
    toggle.focus()

    await user.keyboard('{Enter}')

    await waitFor(() => expect(toggle).toHaveAttribute('aria-checked', 'true'))
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

  it('marks only components with an ACTIVE window, including exact half-open boundaries (AC1)', async () => {
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

  it('coexists with the health badge — a degraded component under active maintenance shows BOTH, non-color-only (AC2)', async () => {
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
