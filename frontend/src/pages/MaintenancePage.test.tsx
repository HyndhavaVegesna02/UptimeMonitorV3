import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_COMPONENTS, FIXTURE_MAINTENANCE_WINDOWS } from '../mocks/handlers'
import { MaintenancePage } from './MaintenancePage'

const NOW = new Date('2026-07-07T10:30:00Z')

const PAST_WINDOW = {
  id: 10,
  component_id: 'sockshop-frontend',
  starts_at: '2026-07-06T09:00:00Z',
  ends_at: '2026-07-06T10:00:00Z',
  reason: 'Past migration',
}
const ACTIVE_WINDOW = {
  id: 11,
  component_id: 'sockshop-catalogue',
  starts_at: '2026-07-07T10:00:00Z',
  ends_at: '2026-07-07T11:00:00Z',
  reason: null,
}
const UPCOMING_WINDOW = {
  id: 12,
  component_id: 'sockshop-orders',
  starts_at: '2026-07-08T09:00:00Z',
  ends_at: '2026-07-08T10:00:00Z',
  reason: 'Planned upgrade',
}

describe('MaintenancePage', () => {
  beforeEach(() => {
    // `vi.setSystemTime` alone (without `vi.useFakeTimers()`) mocks `Date`
    // for the deterministic windowState assertions below WITHOUT freezing
    // real timers — MSW's fetch handling relies on real timers, so faking
    // them would hang every awaited request.
    vi.setSystemTime(NOW)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('shows a loading state, then a table with one row per window (AC1)', async () => {
    render(<MaintenancePage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    for (const window of FIXTURE_MAINTENANCE_WINDOWS) {
      expect(screen.getByText(window.component_id)).toBeInTheDocument()
    }
  })

  it('renders start/end mono and an em-dash for a null reason (AC1, conventions (h))', async () => {
    render(<MaintenancePage />)
    await screen.findByRole('table')

    // FIXTURE_MAINTENANCE_WINDOWS[1] has reason: null.
    const nullReasonWindow = FIXTURE_MAINTENANCE_WINDOWS[1]
    const row = screen.getByText(nullReasonWindow.component_id).closest('tr') as HTMLElement
    expect(within(row).getByText(nullReasonWindow.starts_at)).toHaveClass('text-mono')
    expect(within(row).getByText(nullReasonWindow.ends_at)).toHaveClass('text-mono')
    expect(within(row).getByText('—')).toBeInTheDocument()
  })

  it('derives and renders the correct state badge per the half-open rule (AC1)', async () => {
    server.use(
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json([PAST_WINDOW, ACTIVE_WINDOW, UPCOMING_WINDOW]),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByRole('table')

    const pastRow = screen.getByText(PAST_WINDOW.component_id).closest('tr') as HTMLElement
    expect(within(pastRow).getByText('Past')).toBeInTheDocument()

    const activeRow = screen.getByText(ACTIVE_WINDOW.component_id).closest('tr') as HTMLElement
    expect(within(activeRow).getByText('Active')).toBeInTheDocument()

    const upcomingRow = screen
      .getByText(UPCOMING_WINDOW.component_id)
      .closest('tr') as HTMLElement
    expect(within(upcomingRow).getByText('Upcoming')).toBeInTheDocument()
  })

  it('renders the empty state when no windows are scheduled (AC4)', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json([])))

    render(<MaintenancePage />)

    expect(await screen.findByText('No maintenance scheduled')).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('shows an error state on load failure, then recovers via retry (AC4)', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/maintenance', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
      }),
    )

    render(<MaintenancePage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not load maintenance windows',
    )

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByRole('table')
    expect(callCount).toBe(2)
  })

  it('has labeled, keyboard-operable form inputs using shell primitives (AC4)', async () => {
    const user = userEvent.setup()
    render(<MaintenancePage />)
    await screen.findByRole('table')

    const componentSelect = await screen.findByLabelText('Component')
    const startsInput = screen.getByLabelText('Starts')
    const endsInput = screen.getByLabelText('Ends')
    const reasonInput = screen.getByLabelText('Reason')
    const submitButton = screen.getByRole('button', { name: /schedule window/i })

    await user.selectOptions(componentSelect, FIXTURE_COMPONENTS[0].id)
    expect(componentSelect).toHaveValue(FIXTURE_COMPONENTS[0].id)

    await user.type(reasonInput, 'Routine check')
    expect(reasonInput).toHaveValue('Routine check')

    // Keyboard-operable: Tab reaches every field, in document order.
    startsInput.focus()
    expect(startsInput).toHaveFocus()
    await user.tab()
    expect(endsInput).toHaveFocus()

    expect(submitButton).toBeInTheDocument()
  })

  it('POSTs a tz-aware, well-formed payload and refreshes the list on success (AC2)', async () => {
    const user = userEvent.setup()
    let postedBody: { component_id: string; starts_at: string; ends_at: string; reason: string | null } | undefined
    let getCallCount = 0
    const created = {
      id: 99,
      component_id: FIXTURE_COMPONENTS[0].id,
      starts_at: '2026-07-09T09:00:00.000Z',
      ends_at: '2026-07-09T10:00:00.000Z',
      reason: 'Routine check',
    }
    server.use(
      http.get('/api/v1/maintenance', () => {
        getCallCount += 1
        if (getCallCount === 1) {
          return HttpResponse.json(FIXTURE_MAINTENANCE_WINDOWS)
        }
        return HttpResponse.json([...FIXTURE_MAINTENANCE_WINDOWS, created])
      }),
      http.post('/api/v1/maintenance', async ({ request }) => {
        postedBody = (await request.json()) as typeof postedBody
        return HttpResponse.json(created, { status: 201 })
      }),
    )

    render(<MaintenancePage />)
    await screen.findByRole('table')

    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Starts'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('Ends'), '2026-07-09T10:00')
    await user.type(screen.getByLabelText('Reason'), 'Routine check')

    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    await waitFor(() => expect(getCallCount).toBe(2))
    expect(postedBody).toBeDefined()
    expect(postedBody?.component_id).toBe(FIXTURE_COMPONENTS[0].id)
    // Tz-aware and well-formed (AC2's exact assertion): trailing Z, parses.
    expect(postedBody?.starts_at.endsWith('Z')).toBe(true)
    expect(postedBody?.ends_at.endsWith('Z')).toBe(true)
    expect(Number.isNaN(new Date(postedBody!.starts_at).getTime())).toBe(false)
    expect(Number.isNaN(new Date(postedBody!.ends_at).getTime())).toBe(false)
    // Matches the local-time input interpreted via the documented conversion.
    expect(postedBody?.starts_at).toBe(new Date('2026-07-09T09:00').toISOString())
    expect(postedBody?.ends_at).toBe(new Date('2026-07-09T10:00').toISOString())

    // Refreshed list now includes the newly-created window.
    await screen.findByText(created.reason as string)
  })

  it('renders a naive-starts_at 422 INLINE next to the Starts field, not toast/console-only (AC3)', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'starts_at must be timezone-aware.' }, { status: 422 }),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByRole('table')

    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Starts'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('Ends'), '2026-07-09T10:00')
    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    const startsField = screen.getByLabelText('Starts').closest('.maintenance-form__field')
    expect(startsField).not.toBeNull()
    expect(
      await within(startsField as HTMLElement).findByText('starts_at must be timezone-aware.'),
    ).toBeInTheDocument()
  })

  it('renders an empty-component_id 422 INLINE next to the Component field (AC3)', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json(
          { detail: 'component_id must be a non-empty string.' },
          { status: 422 },
        ),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByRole('table')

    // A component IS chosen client-side (the select's own `required` would
    // otherwise block submission); the server-side 422 is exercised purely
    // via the mocked response, independent of what was actually submitted —
    // the point under test is the detail->field MAPPING, not reproducing
    // the exact browser state that would trigger this specific backend rule.
    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Starts'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('Ends'), '2026-07-09T10:00')
    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    const componentField = screen
      .getByLabelText('Component')
      .closest('.maintenance-form__field')
    expect(componentField).not.toBeNull()
    expect(
      await within(componentField as HTMLElement).findByText(
        'component_id must be a non-empty string.',
      ),
    ).toBeInTheDocument()
  })

  it('renders an ends_at<=starts_at 422 INLINE next to the Ends field, not the Component field (STORY-052 AC2)', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json(
          { detail: 'ends_at must be strictly greater than starts_at.' },
          { status: 422 },
        ),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByRole('table')

    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Starts'), '2026-07-09T10:00')
    await user.type(screen.getByLabelText('Ends'), '2026-07-09T09:00')
    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    const endsField = screen.getByLabelText('Ends').closest('.maintenance-form__field')
    expect(endsField).not.toBeNull()
    expect(
      await within(endsField as HTMLElement).findByText(
        'ends_at must be strictly greater than starts_at.',
      ),
    ).toBeInTheDocument()

    const componentField = screen
      .getByLabelText('Component')
      .closest('.maintenance-form__field')
    expect(componentField).not.toBeNull()
    expect(
      within(componentField as HTMLElement).queryByText(
        'ends_at must be strictly greater than starts_at.',
      ),
    ).not.toBeInTheDocument()
  })
})
