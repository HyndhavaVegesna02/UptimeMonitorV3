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

/** Finds the `<li>` ancestor of a piece of text rendered in the windows
 * list — mirrors the old table's `closest('tr')` helper, adapted to the
 * STORY-061 two-column list markup. */
function windowItemFor(text: string): HTMLElement {
  const node = screen.getByText(text)
  const item = node.closest('li')
  if (!item) {
    throw new Error(`no <li> ancestor found for text "${text}"`)
  }
  return item as HTMLElement
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

  it('renders a two-column layout: a "New window" form card + a windows list (AC1)', async () => {
    render(<MaintenancePage />)

    expect(screen.getByRole('heading', { name: 'Maintenance', level: 1 })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'New window', level: 2 })).toBeInTheDocument()

    expect(screen.getByRole('status')).toBeInTheDocument()

    for (const window of FIXTURE_MAINTENANCE_WINDOWS) {
      expect(await screen.findByText(window.component_id)).toBeInTheDocument()
    }
  })

  it('renders each window as title/reason + state badge + "component · range" (AC1)', async () => {
    render(<MaintenancePage />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    // FIXTURE_MAINTENANCE_WINDOWS[1] has reason: null -> em-dash title.
    const nullReasonWindow = FIXTURE_MAINTENANCE_WINDOWS[1]
    const item = windowItemFor(nullReasonWindow.component_id)
    expect(within(item).getByText('—')).toBeInTheDocument()
    expect(
      within(item).getByText(
        `${nullReasonWindow.starts_at}–${nullReasonWindow.ends_at}`,
      ),
    ).toBeInTheDocument()

    // The other fixture window has a real reason string, rendered as its title.
    const namedWindow = FIXTURE_MAINTENANCE_WINDOWS[0]
    const namedItem = windowItemFor(namedWindow.component_id)
    expect(within(namedItem).getByText(namedWindow.reason as string)).toBeInTheDocument()
  })

  it('derives and renders the correct state badge per the half-open rule (AC1)', async () => {
    server.use(
      http.get('/api/v1/maintenance', () =>
        HttpResponse.json([PAST_WINDOW, ACTIVE_WINDOW, UPCOMING_WINDOW]),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByText(PAST_WINDOW.component_id)

    expect(within(windowItemFor(PAST_WINDOW.component_id)).getByText('Past')).toBeInTheDocument()
    expect(
      within(windowItemFor(ACTIVE_WINDOW.component_id)).getByText('Active'),
    ).toBeInTheDocument()
    expect(
      within(windowItemFor(UPCOMING_WINDOW.component_id)).getByText('Upcoming'),
    ).toBeInTheDocument()
  })

  it('never renders a delete control on a window (AC3 — omitted, no DELETE endpoint)', async () => {
    render(<MaintenancePage />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument()
  })

  it('renders the empty state when no windows are scheduled (AC4)', async () => {
    server.use(http.get('/api/v1/maintenance', () => HttpResponse.json([])))

    render(<MaintenancePage />)

    expect(await screen.findByText('No maintenance scheduled')).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: /window/i })).not.toBeInTheDocument()
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

    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)
    expect(callCount).toBe(2)
  })

  it('has labeled, keyboard-operable form inputs in mock order: Title, Component, Start, End (AC1, AC4)', async () => {
    const user = userEvent.setup()
    render(<MaintenancePage />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    const titleInput = screen.getByLabelText('Title')
    const componentSelect = await screen.findByLabelText('Component')
    const startInput = screen.getByLabelText('Start')
    const endInput = screen.getByLabelText('End')
    const submitButton = screen.getByRole('button', { name: /schedule window/i })

    await user.type(titleInput, 'Routine check')
    expect(titleInput).toHaveValue('Routine check')

    await user.selectOptions(componentSelect, FIXTURE_COMPONENTS[0].id)
    expect(componentSelect).toHaveValue(FIXTURE_COMPONENTS[0].id)

    // Keyboard-operable, mock order: Title -> Component -> Start -> End -> submit.
    titleInput.focus()
    expect(titleInput).toHaveFocus()
    await user.tab()
    expect(componentSelect).toHaveFocus()
    await user.tab()
    expect(startInput).toHaveFocus()
    await user.tab()
    expect(endInput).toHaveFocus()

    expect(submitButton).toBeInTheDocument()
  })

  it('POSTs a tz-aware payload with Title mapped to reason, refreshes the list, and resets the form on success (AC1, AC2)', async () => {
    const user = userEvent.setup()
    let postedBody:
      | { component_id: string; starts_at: string; ends_at: string; reason: string | null }
      | undefined
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
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    const titleInput = screen.getByLabelText('Title')
    const componentSelect = await screen.findByLabelText('Component')

    await user.type(titleInput, 'Routine check')
    await user.selectOptions(componentSelect, FIXTURE_COMPONENTS[0].id)
    await user.type(screen.getByLabelText('Start'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('End'), '2026-07-09T10:00')

    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    await waitFor(() => expect(getCallCount).toBe(2))
    expect(postedBody).toBeDefined()
    expect(postedBody?.component_id).toBe(FIXTURE_COMPONENTS[0].id)
    // Title -> reason mapping (AC1: the DTO has no separate title field).
    expect(postedBody?.reason).toBe('Routine check')
    // Tz-aware and well-formed (AC2): trailing Z, parses.
    expect(postedBody?.starts_at.endsWith('Z')).toBe(true)
    expect(postedBody?.ends_at.endsWith('Z')).toBe(true)
    expect(Number.isNaN(new Date(postedBody!.starts_at).getTime())).toBe(false)
    expect(Number.isNaN(new Date(postedBody!.ends_at).getTime())).toBe(false)
    // Matches the local-time input interpreted via the documented conversion.
    expect(postedBody?.starts_at).toBe(new Date('2026-07-09T09:00').toISOString())
    expect(postedBody?.ends_at).toBe(new Date('2026-07-09T10:00').toISOString())

    // Refreshed list now includes the newly-created window.
    await screen.findByText(created.reason)

    // Form resets on success (AC2).
    expect(screen.getByLabelText('Title')).toHaveValue('')
    expect(screen.getByLabelText('Component')).toHaveValue('')
    expect(screen.getByLabelText('Start')).toHaveValue('')
    expect(screen.getByLabelText('End')).toHaveValue('')
  })

  it('renders a naive-starts_at 422 INLINE next to the Start field, not toast/console-only (AC2)', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'starts_at must be timezone-aware.' }, { status: 422 }),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Start'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('End'), '2026-07-09T10:00')
    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    const startField = screen.getByLabelText('Start').closest('.maintenance-form__field')
    expect(startField).not.toBeNull()
    expect(
      await within(startField as HTMLElement).findByText('starts_at must be timezone-aware.'),
    ).toBeInTheDocument()
  })

  it('renders an empty-component_id 422 INLINE next to the Component field (AC2)', async () => {
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
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    // A component IS chosen client-side (the select's own `required` would
    // otherwise block submission); the server-side 422 is exercised purely
    // via the mocked response, independent of what was actually submitted —
    // the point under test is the detail->field MAPPING, not reproducing
    // the exact browser state that would trigger this specific backend rule.
    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Start'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('End'), '2026-07-09T10:00')
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

  it('renders an ends_at<=starts_at 422 INLINE next to the End field, not the Component field (AC2)', async () => {
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
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Start'), '2026-07-09T10:00')
    await user.type(screen.getByLabelText('End'), '2026-07-09T09:00')
    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    const endField = screen.getByLabelText('End').closest('.maintenance-form__field')
    expect(endField).not.toBeNull()
    expect(
      await within(endField as HTMLElement).findByText(
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

  it('falls back to a form-level error when the 422 detail names no known field (AC2)', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/maintenance', () =>
        HttpResponse.json({ detail: 'something unexpected happened' }, { status: 422 }),
      ),
    )

    render(<MaintenancePage />)
    await screen.findByText(FIXTURE_MAINTENANCE_WINDOWS[0].component_id)

    await user.selectOptions(
      await screen.findByLabelText('Component'),
      FIXTURE_COMPONENTS[0].id,
    )
    await user.type(screen.getByLabelText('Start'), '2026-07-09T09:00')
    await user.type(screen.getByLabelText('End'), '2026-07-09T10:00')
    await user.click(screen.getByRole('button', { name: /schedule window/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('something unexpected happened')
  })
})
