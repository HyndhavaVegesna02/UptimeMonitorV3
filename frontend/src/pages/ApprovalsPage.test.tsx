import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { server } from '../mocks/server'
import {
  FIXTURE_HISTORY_FRONTEND_HTTP,
  FIXTURE_PROPOSALS,
  FIXTURE_TOPOLOGY,
} from '../mocks/handlers'
import { getActor } from '../api/actor'
import { ApprovalsPage } from './ApprovalsPage'

/** Renders `ApprovalsPage` inside a `MemoryRouter` — required as of
 * STORY-100 since each card's "View checks" affordance renders as a real
 * routed `Link`, which throws outside a Router (mirrors
 * `DashboardPage.test.tsx`'s `renderDashboard` helper, STORY-099). */
function renderApprovalsPage() {
  return render(
    <MemoryRouter>
      <ApprovalsPage />
    </MemoryRouter>,
  )
}

describe('ApprovalsPage', () => {
  afterEach(() => {
    // A no-op unless a test below sets a fixed system time (STORY-098's
    // proposed_at relative-time test) — safe to call unconditionally.
    vi.useRealTimers()
  })

  it('renders the h1 via the shared PageHeader, outside the card, in the shared narrow container (STORY-097 AC1, AC2)', async () => {
    const { container } = renderApprovalsPage()

    const heading = screen.getByRole('heading', { name: 'Approvals', level: 1 })
    expect(heading.closest('.page-header')).not.toBeNull()

    const root = container.querySelector('.approvals-page')
    expect(root).toHaveClass('page')
    expect(root).not.toHaveClass('page--wide')
  })

  it('shows a loading state, then one card per open proposal (AC1)', async () => {
    renderApprovalsPage()

    expect(screen.getByRole('status')).toBeInTheDocument()

    const list = await screen.findByRole('list')
    expect(list).toBeInTheDocument()

    expect(screen.getByText(FIXTURE_PROPOSALS[0].component_id)).toBeInTheDocument()
    expect(screen.getByText(FIXTURE_PROPOSALS[1].component_id)).toBeInTheDocument()

    // Exactly one card per fixture proposal.
    expect(within(list).getAllByRole('listitem')).toHaveLength(FIXTURE_PROPOSALS.length)
  })

  it('renders a severity chip derived from to_status, not a fake field (AC1)', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    // FIXTURE_PROPOSALS[0].to_status === 'degraded' -> "Degraded" severity,
    // which also happens to be the to-status StatusBadge's own label text —
    // both are legitimately present, hence getAllByText/length 2 (one is the
    // severity chip, one is the StatusBadge label).
    const degradedCard = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest('li')
    expect(degradedCard).not.toBeNull()
    const degradedMatches = within(degradedCard as HTMLElement).getAllByText('Degraded')
    expect(degradedMatches).toHaveLength(2)
    expect(
      degradedMatches.some((el) => el.classList.contains('approval-card__severity')),
    ).toBe(true)

    // FIXTURE_PROPOSALS[1].to_status === 'major_outage' -> "Major" severity.
    const majorCard = screen.getByText(FIXTURE_PROPOSALS[1].component_id).closest('li')
    expect(majorCard).not.toBeNull()
    expect(within(majorCard as HTMLElement).getByText('Major')).toBeInTheDocument()
  })

  it('renders both StatusBadges for an ordinary transition (AC1)', async () => {
    renderApprovalsPage()

    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest('li')
    expect(card).not.toBeNull()
    // operational -> "Up", degraded -> "Degraded" (src/api/statusMapping.ts).
    // "Degraded" also matches the severity chip (same word, different
    // element) — assert two occurrences rather than a single unique match.
    expect(within(card as HTMLElement).getByText('Up')).toBeInTheDocument()
    expect(within(card as HTMLElement).getAllByText('Degraded')).toHaveLength(2)
  })

  it('handles a null from_status without crashing, rendering "New" instead of a badge (AC1)', async () => {
    renderApprovalsPage()

    await screen.findByRole('list')

    const card = screen.getByText(FIXTURE_PROPOSALS[1].component_id).closest('li')
    expect(card).not.toBeNull()
    expect(within(card as HTMLElement).getByText('New')).toBeInTheDocument()
    expect(within(card as HTMLElement).getByText('Down')).toBeInTheDocument()
    // No StatusBadge label rendered for the null from_status.
    expect(within(card as HTMLElement).queryByText('Unknown')).not.toBeInTheDocument()
  })

  it('renders the proposed_at instant as relative time, in monospace, with the raw instant preserved (AC1, AC2, STORY-098)', async () => {
    // Fixed 2 hours after the first fixture's proposed_at, so the relative
    // text is deterministic.
    vi.setSystemTime(new Date('2026-07-01T14:00:00Z'))

    renderApprovalsPage()
    await screen.findByRole('list')

    const time = screen.getByText('2h ago')
    expect(time.tagName).toBe('TIME')
    expect(time).toHaveClass('text-mono')
    expect(time).toHaveAttribute('dateTime', FIXTURE_PROPOSALS[0].proposed_at)
    expect(time.getAttribute('title')).toContain(
      new Date(FIXTURE_PROPOSALS[0].proposed_at).toISOString(),
    )
    // AC1: no bare ISO-8601 string as primary text.
    expect(screen.queryByText(FIXTURE_PROPOSALS[0].proposed_at)).not.toBeInTheDocument()
  })

  it('does not render fields the API does not expose — no reason/source/checks/signals copy (AC3)', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    expect(screen.queryByText(/triggering signals/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/detected/i)).not.toBeInTheDocument()
  })

  it('resolves the friendly component name from topology, keeping the raw component_id as a secondary slug (STORY-100 AC1)', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    // FIXTURE_PROPOSALS[0].component_id === FIXTURE_TOPOLOGY[0].id.
    const friendlyName = FIXTURE_TOPOLOGY[0].name
    const card = screen.getByText(friendlyName).closest('li')
    expect(card).not.toBeNull()
    expect(
      within(card as HTMLElement).getByText(FIXTURE_PROPOSALS[0].component_id),
    ).toBeInTheDocument()
  })

  it('renders per-location evidence rows (status, latency, relative time) for the component\'s primary signal (STORY-100 AC1)', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen
      .getByText(FIXTURE_TOPOLOGY[0].name)
      .closest('li') as HTMLElement

    // FIXTURE_HISTORY_FRONTEND_HTTP has 3 distinct locations.
    const locationRows = await within(card).findAllByText(/^Location …/)
    expect(locationRows).toHaveLength(3)

    // First row: location …0060, "Up" status, 571 ms latency.
    const firstRow = locationRows[0].closest('li') as HTMLElement
    expect(within(firstRow).getByText('Up')).toBeInTheDocument()
    expect(within(firstRow).getByText('571 ms')).toBeInTheDocument()
    const time = within(firstRow).getByText(/ago|just now/)
    expect(time.tagName).toBe('TIME')
    expect(time).toHaveAttribute('dateTime', FIXTURE_HISTORY_FRONTEND_HTTP[0].observed_at)
  })

  it('shows a quiet "evidence unavailable" note on a history-fetch failure, and the card stays fully actionable (STORY-100 AC4)', async () => {
    server.use(
      http.get('/api/v1/history', () =>
        HttpResponse.json({ detail: 'boom' }, { status: 500 }),
      ),
    )

    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen
      .getByText(FIXTURE_TOPOLOGY[0].name)
      .closest('li') as HTMLElement

    expect(await within(card).findByText('Evidence unavailable')).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('renders each proposal card\'s evidence independently — one card\'s failure does not affect another\'s (STORY-100 AC4)', async () => {
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

    const frontendCard = screen
      .getByText(FIXTURE_TOPOLOGY[0].name)
      .closest('li') as HTMLElement
    const catalogueCard = screen
      .getByText(FIXTURE_TOPOLOGY[1].name)
      .closest('li') as HTMLElement

    expect(await within(frontendCard).findAllByText(/^Location …/)).toHaveLength(3)
    expect(await within(catalogueCard).findByText('Evidence unavailable')).toBeInTheDocument()
  })

  it('renders a "View checks" link deep-linking to Check History pre-filtered to the primary signal (STORY-100 AC2)', async () => {
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen
      .getByText(FIXTURE_TOPOLOGY[0].name)
      .closest('li') as HTMLElement

    const link = within(card).getByRole('link', { name: 'View checks' })
    expect(link).toHaveAttribute(
      'href',
      `/check-history?signal=${FIXTURE_TOPOLOGY[0].signals[0].signal_key}`,
    )
  })

  it('omits the "View checks" link when no signal is resolved (topology failure), keeping the card actionable (STORY-100 AC2, AC4)', async () => {
    server.use(http.get('/api/v1/topology', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))

    renderApprovalsPage()
    const list = await screen.findByRole('list')
    // Component name unresolved -> falls back to the raw component_id in
    // BOTH the name and slug spans, so locate the card positionally
    // (FIXTURE_PROPOSALS[0] is the first card) instead of by text.
    const card = within(list).getAllByRole('listitem')[0]

    expect(within(card).queryByRole('link', { name: 'View checks' })).not.toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
  })

  it('shows the "Queue clear" empty state when there are no open proposals (AC3)', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))

    renderApprovalsPage()

    expect(await screen.findByText('Queue clear')).toBeInTheDocument()
    expect(screen.queryByRole('list')).not.toBeInTheDocument()
  })

  it('uses the shared EmptyState primitive for "Queue clear", with a helpful body line (STORY-097 AC3)', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))

    const { container } = renderApprovalsPage()

    const message = await screen.findByText('Queue clear')
    expect(message.closest('.empty-state')).not.toBeNull()
    expect(container.querySelector('.empty-state__icon--positive')).not.toBeNull()
    expect(screen.getByText('No proposals awaiting review.')).toBeInTheDocument()
  })

  it('shows an error state on load failure, then recovers via retry (AC4)', async () => {
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

  it('renders an Approve and a Reject action per open proposal (AC1, AC2)', async () => {
    renderApprovalsPage()

    await screen.findByRole('list')

    for (const proposal of FIXTURE_PROPOSALS) {
      const card = screen.getByText(proposal.component_id).closest('li')
      expect(card).not.toBeNull()
      expect(
        within(card as HTMLElement).getByRole('button', { name: 'Approve' }),
      ).toBeInTheDocument()
      expect(
        within(card as HTMLElement).getByRole('button', { name: 'Reject' }),
      ).toBeInTheDocument()
    }
  })

  it('requires confirmation before POSTing an approve, then refreshes the list on success (AC2)', async () => {
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

    const card = screen.getByText(target.component_id).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))

    // Confirmation precedes the POST: no request fired yet by clicking Approve.
    expect(postedBody).toBeUndefined()

    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    await waitFor(() =>
      expect(screen.queryByText(target.component_id)).not.toBeInTheDocument(),
    )
    expect(postedBody).toEqual({ action: 'approve', actor: getActor() })
    expect(getCallCount).toBe(2)
  })

  it('requires confirmation before POSTing a reject, then refreshes the list on success (AC2)', async () => {
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

    const card = screen.getByText(target.component_id).closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Reject' }))

    await user.click(await screen.findByRole('button', { name: 'Confirm reject' }))

    await waitFor(() =>
      expect(screen.queryByText(target.component_id)).not.toBeInTheDocument(),
    )
    expect(postedBody).toEqual({ action: 'reject', actor: getActor() })
    expect(getCallCount).toBe(2)
  })

  it('lets the operator dismiss the confirmation step without POSTing (AC2)', async () => {
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

    const card = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))

    await user.click(await screen.findByRole('button', { name: 'Cancel' }))

    expect(screen.queryByRole('button', { name: 'Confirm approve' })).not.toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(postCalled).toBe(false)
  })

  it('is keyboard-operable: Enter on a focused Approve button opens the confirmation (AC2)', async () => {
    const user = userEvent.setup()
    renderApprovalsPage()
    await screen.findByRole('list')

    const card = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('li') as HTMLElement
    const approveButton = within(card).getByRole('button', { name: 'Approve' })
    approveButton.focus()
    await user.keyboard('{Enter}')

    expect(await screen.findByRole('button', { name: 'Confirm approve' })).toBeInTheDocument()
  })

  it('shows an inline "already resolved" message and refreshes the list on a 409 lost race (AC2)', async () => {
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

    const card = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    expect(await screen.findByText(/already been resolved/i)).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent(/already been resolved/i)
    await waitFor(() => expect(getCallCount).toBe(2))
  })

  it('shows an inline "no longer exists" message and refreshes the list on a 404 (AC2)', async () => {
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

    const card = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Reject' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm reject' }))

    expect(await screen.findByText(/no longer exists/i)).toBeInTheDocument()
    await waitFor(() => expect(getCallCount).toBe(2))
  })

  it('shows the shell ErrorState with retry on a generic decision failure, and retry re-attempts the POST (AC2)', async () => {
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

    const card = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('li') as HTMLElement
    await user.click(within(card).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
    // The list refresh (triggered by the successful retry) unmounts and
    // remounts the cards, so re-locate the card instead of reusing the
    // pre-refresh reference.
    await screen.findByRole('list')
    const refreshedCard = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('li') as HTMLElement
    expect(within(refreshedCard).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(attempt).toBe(2)
  })
})
