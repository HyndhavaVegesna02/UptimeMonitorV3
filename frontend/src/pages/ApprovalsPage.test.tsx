import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_HISTORY_FRONTEND_HTTP, FIXTURE_PROPOSALS, FIXTURE_TOPOLOGY } from '../mocks/handlers'
import { getActor } from '../api/actor'
import { ApprovalsPage } from './ApprovalsPage'

/** `ApprovalCard`'s "View checks" affordance renders as a real routed
 * `Link`, which throws outside a Router (mirrors `DashboardPage.test.tsx`'s
 * `renderPage` helper). */
function renderApprovalsPage() {
  return render(
    <MemoryRouter>
      <ApprovalsPage />
    </MemoryRouter>,
  )
}

describe('ApprovalsPage — layout', () => {
  afterEach(() => {
    vi.useRealTimers()
  })

  it('renders exactly one h1 titled Approvals', () => {
    renderApprovalsPage()
    expect(screen.getByRole('heading', { name: 'Approvals', level: 1 })).toBeInTheDocument()
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
  })

  it('shows a loading state, then one card per open proposal (AC1)', async () => {
    renderApprovalsPage()

    expect(screen.getByRole('status')).toBeInTheDocument()

    const list = await screen.findByRole('list')
    expect(within(list).getAllByRole('listitem')).toHaveLength(FIXTURE_PROPOSALS.length)
  })
})

describe('ApprovalsPage — card anatomy (AC1)', () => {
  it('resolves the friendly component name from topology, keeping the raw component_id as a secondary slug', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const friendlyName = FIXTURE_TOPOLOGY[0].name
    const card = screen.getByText(friendlyName).closest('li') as HTMLElement
    expect(within(card).getByText(FIXTURE_PROPOSALS[0].component_id)).toBeInTheDocument()
  })

  it('renders a severity label derived from to_status, not a fake field', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    // FIXTURE_PROPOSALS[0].to_status === 'degraded' -> "Degraded" severity,
    // which also happens to be the to-status StatusBadge's own label text.
    const degradedCard = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    const degradedMatches = within(degradedCard).getAllByText('Degraded')
    expect(degradedMatches.length).toBeGreaterThanOrEqual(2)

    // FIXTURE_PROPOSALS[1].to_status === 'major_outage' -> "Major" severity.
    const majorCard = screen.getByText(FIXTURE_TOPOLOGY[1].name).closest('li') as HTMLElement
    expect(within(majorCard).getByText('Major')).toBeInTheDocument()
  })

  it('renders both StatusBadges for an ordinary from -> to transition', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    // operational -> "Up", degraded -> "Degraded" (also matches the
    // severity label, hence getAllByText).
    expect(within(card).getByText('Up')).toBeInTheDocument()
    expect(within(card).getAllByText('Degraded').length).toBeGreaterThanOrEqual(1)
  })

  it('handles a null from_status without crashing, rendering "New" instead of a badge', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[1].name).closest('li') as HTMLElement
    expect(within(card).getByText('New')).toBeInTheDocument()
    expect(within(card).getByText('Down')).toBeInTheDocument()
    expect(within(card).queryByText('Unknown')).not.toBeInTheDocument()
  })

  it('renders the proposed_at instant as relative time, with the raw instant preserved', async () => {
    vi.setSystemTime(new Date('2026-07-01T14:00:00Z'))

    renderApprovalsPage()
    await screen.findByRole('list')

    const time = screen.getByText('2h ago')
    expect(time.tagName).toBe('TIME')
    expect(time).toHaveAttribute('dateTime', FIXTURE_PROPOSALS[0].proposed_at)
    expect(screen.queryByText(FIXTURE_PROPOSALS[0].proposed_at)).not.toBeInTheDocument()
  })

  it('renders per-location evidence rows (status, latency, relative time) for the primary signal (AC1)', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement

    // FIXTURE_HISTORY_FRONTEND_HTTP has 3 distinct locations.
    const locationRows = await within(card).findAllByText(/^Location …/)
    expect(locationRows).toHaveLength(3)

    const firstRow = locationRows[0].closest('li') as HTMLElement
    expect(within(firstRow).getByText('Up')).toBeInTheDocument()
    expect(within(firstRow).getByText('571 ms')).toBeInTheDocument()
    const time = firstRow.querySelector('time') as HTMLElement
    expect(time.tagName).toBe('TIME')
    expect(time).toHaveAttribute('dateTime', FIXTURE_HISTORY_FRONTEND_HTTP[0].observed_at)
  })

  it('shows a static skeleton while evidence is loading', async () => {
    server.use(
      http.get('/api/v1/history', async () => {
        await new Promise((resolve) => setTimeout(resolve, 20))
        return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
      }),
    )

    const { container } = renderApprovalsPage()
    await screen.findByRole('list')

    expect(container.querySelector('.approval-card__evidence-skeleton')).toBeInTheDocument()

    await screen.findAllByText(/^Location …/)
  })

  it('shows a quiet "Evidence unavailable" note on a history-fetch failure, card stays fully actionable (AC1, AC4)', async () => {
    server.use(
      http.get('/api/v1/history', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement

    expect(await within(card).findByText('Evidence unavailable')).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('shows "No recent checks recorded" when the signal genuinely has no observations', async () => {
    server.use(http.get('/api/v1/history', () => HttpResponse.json([])))

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    expect(await within(card).findByText('No recent checks recorded')).toBeInTheDocument()
  })

  it("renders each card's evidence independently — one card's failure does not affect another's (AC4)", async () => {
    server.use(
      http.get('/api/v1/history', ({ request }) => {
        const url = new URL(request.url)
        const signalKey = url.searchParams.get('signal_key')
        if (signalKey === 'frontend-http') {
          return HttpResponse.json(FIXTURE_HISTORY_FRONTEND_HTTP)
        }
        return HttpResponse.json({ detail: 'boom' }, { status: 500 })
      }),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const frontendCard = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    const catalogueCard = screen.getByText(FIXTURE_TOPOLOGY[1].name).closest('li') as HTMLElement

    expect(await within(frontendCard).findAllByText(/^Location …/)).toHaveLength(3)
    expect(await within(catalogueCard).findByText('Evidence unavailable')).toBeInTheDocument()
  })

  it('does not render fields the API does not expose — no reason/triggering-signals copy', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    expect(screen.queryByText(/triggering signals/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/detected/i)).not.toBeInTheDocument()
  })
})

describe('ApprovalsPage — View checks deep link (AC2)', () => {
  it('renders a "View checks" link deep-linking to Check History pre-filtered to the primary signal', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    const link = within(card).getByRole('link', { name: 'View checks' })
    expect(link).toHaveAttribute(
      'href',
      `/check-history?signal=${FIXTURE_TOPOLOGY[0].signals[0].signal_key}`,
    )
  })

  it('omits the "View checks" link when no signal is resolved (topology failure), card stays actionable', async () => {
    server.use(
      http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )

    renderApprovalsPage()
    const list = await screen.findByRole('list')
    const card = within(list).getAllByRole('listitem')[0]

    expect(within(card).queryByRole('link', { name: 'View checks' })).not.toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
  })
})

describe('ApprovalsPage — approve/reject confirm flow (AC3)', () => {
  it('states the publish consequence (component + target status) on the approve confirm step', async () => {
    const user = userEvent.setup()
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))

    expect(
      await within(card).findByText(
        "Publishes 'Sock Shop — frontend: Degraded' to the public status page.",
      ),
    ).toBeInTheDocument()
  })

  it('leaves the reject confirm prompt unchanged', async () => {
    const user = userEvent.setup()
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[1].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Reject' }))

    expect(await within(card).findByText('Reject this proposal?')).toBeInTheDocument()
  })

  it('requires confirmation before POSTing an approve, then refreshes the list on success', async () => {
    const user = userEvent.setup()
    const target = FIXTURE_PROPOSALS[0]
    let postedBody: unknown
    let getCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        getCallCount += 1
        if (getCallCount === 1) {
          return HttpResponse.json(FIXTURE_PROPOSALS)
        }
        return HttpResponse.json(FIXTURE_PROPOSALS.filter((p) => p.id !== target.id))
      }),
      http.post('/api/v1/decisions/:proposalId', async ({ request, params }) => {
        postedBody = await request.json()
        return HttpResponse.json({
          proposal_id: Number(params.proposalId),
          state: 'approved',
          resolved_at: '2026-07-02T09:00:00Z',
        })
      }),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))

    expect(postedBody).toBeUndefined()

    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    await waitFor(() =>
      expect(screen.queryByText(target.component_id)).not.toBeInTheDocument(),
    )
    expect(postedBody).toEqual({ action: 'approve', actor: getActor() })
    expect(getCallCount).toBe(2)
  })

  it('requires confirmation before POSTing a reject, then refreshes the list on success', async () => {
    const user = userEvent.setup()
    const target = FIXTURE_PROPOSALS[1]
    let postedBody: unknown
    let getCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        getCallCount += 1
        if (getCallCount === 1) {
          return HttpResponse.json(FIXTURE_PROPOSALS)
        }
        return HttpResponse.json(FIXTURE_PROPOSALS.filter((p) => p.id !== target.id))
      }),
      http.post('/api/v1/decisions/:proposalId', async ({ request, params }) => {
        postedBody = await request.json()
        return HttpResponse.json({
          proposal_id: Number(params.proposalId),
          state: 'rejected',
          resolved_at: '2026-07-02T09:00:00Z',
        })
      }),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[1].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Reject' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm reject' }))

    await waitFor(() =>
      expect(screen.queryByText(target.component_id)).not.toBeInTheDocument(),
    )
    expect(postedBody).toEqual({ action: 'reject', actor: getActor() })
    expect(getCallCount).toBe(2)
  })

  it('lets the operator dismiss the confirmation step without POSTing', async () => {
    const user = userEvent.setup()
    let postCalled = false
    server.use(
      http.post('/api/v1/decisions/:proposalId', () => {
        postCalled = true
        return HttpResponse.json({
          proposal_id: FIXTURE_PROPOSALS[0].id,
          state: 'approved',
          resolved_at: '2026-07-02T09:00:00Z',
        })
      }),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Cancel' }))

    expect(screen.queryByRole('button', { name: 'Confirm approve' })).not.toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(postCalled).toBe(false)
  })

  it('disables actions and shows a submitting state while the decision POST is in flight', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/api/v1/decisions/:proposalId', async () => {
        await new Promise((resolve) => setTimeout(resolve, 30))
        return HttpResponse.json({
          proposal_id: FIXTURE_PROPOSALS[0].id,
          state: 'approved',
          resolved_at: '2026-07-02T09:00:00Z',
        })
      }),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    const confirmButton = await within(card).findByRole('button', { name: 'Confirm approve' })
    expect(confirmButton).toBeDisabled()
    expect(confirmButton).toHaveAttribute('aria-busy', 'true')
    expect(within(card).getByRole('button', { name: 'Cancel' })).toBeDisabled()
  })

  it('shows an inline "already resolved" message and refreshes the list on a 409 lost race', async () => {
    const user = userEvent.setup()
    let getCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        getCallCount += 1
        return HttpResponse.json(FIXTURE_PROPOSALS)
      }),
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'not open' }, { status: 409 }),
      ),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    expect(await screen.findByText(/already been resolved/i)).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(/already been resolved/i)
    await waitFor(() => expect(getCallCount).toBe(2))
  })

  it('shows an inline "no longer exists" message and refreshes the list on a 404', async () => {
    const user = userEvent.setup()
    let getCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        getCallCount += 1
        return HttpResponse.json(FIXTURE_PROPOSALS)
      }),
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'not found' }, { status: 404 }),
      ),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[1].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Reject' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm reject' }))

    expect(await screen.findByText(/no longer exists/i)).toBeInTheDocument()
    await waitFor(() => expect(getCallCount).toBe(2))
  })

  it('shows a retryable error on a generic decision failure, and retry re-attempts the POST', async () => {
    const user = userEvent.setup()
    let attempt = 0
    server.use(
      http.post('/api/v1/decisions/:proposalId', () => {
        attempt += 1
        if (attempt === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json({
          proposal_id: FIXTURE_PROPOSALS[0].id,
          state: 'approved',
          resolved_at: '2026-07-02T09:00:00Z',
        })
      }),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
    await screen.findByRole('list')
    const refreshedCard = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    expect(within(refreshedCard).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(attempt).toBe(2)
  })

  it('is keyboard-operable: Enter on a focused Approve button opens the confirmation', async () => {
    const user = userEvent.setup()
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_TOPOLOGY[0].name).closest('li') as HTMLElement
    const approveButton = within(card).getByRole('button', { name: 'Approve' })
    approveButton.focus()
    await user.keyboard('{Enter}')

    expect(await screen.findByRole('button', { name: 'Confirm approve' })).toBeInTheDocument()
  })
})

describe('ApprovalsPage — empty/error states (AC1, AC4)', () => {
  it('shows the "Queue clear" empty state when there are no open proposals', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))

    renderApprovalsPage()

    expect(await screen.findByText('Queue clear')).toBeInTheDocument()
    expect(screen.getByText('No proposals awaiting review.')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('shows an error state on load failure, then recovers via retry', async () => {
    const user = userEvent.setup()
    let callCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        callCount += 1
        if (callCount === 1) {
          return HttpResponse.json({ detail: 'boom' }, { status: 500 })
        }
        return HttpResponse.json(FIXTURE_PROPOSALS)
      }),
    )

    renderApprovalsPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not load proposals')

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByRole('list')
    expect(callCount).toBe(2)
  })
})
