import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_PROPOSALS } from '../mocks/handlers'
import { getActor } from '../api/actor'
import { ApprovalsPage } from './ApprovalsPage'

describe('ApprovalsPage', () => {
  it('shows a loading state, then a table with one row per open proposal (AC1)', async () => {
    render(<ApprovalsPage />)

    expect(screen.getByRole('status')).toBeInTheDocument()

    const table = await screen.findByRole('table')
    expect(table).toBeInTheDocument()

    expect(
      screen.getByText(FIXTURE_PROPOSALS[0].component_id),
    ).toBeInTheDocument()
    expect(
      screen.getByText(FIXTURE_PROPOSALS[1].component_id),
    ).toBeInTheDocument()

    // Exactly one data row per fixture proposal.
    expect(screen.getAllByRole('row')).toHaveLength(FIXTURE_PROPOSALS.length + 1)
  })

  it('renders both StatusBadges for an ordinary transition (AC1)', async () => {
    render(<ApprovalsPage />)

    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest('tr')
    expect(row).not.toBeNull()
    // operational -> "Up", degraded -> "Degraded" (src/api/statusMapping.ts)
    expect(within(row as HTMLElement).getByText('Up')).toBeInTheDocument()
    expect(within(row as HTMLElement).getByText('Degraded')).toBeInTheDocument()
  })

  it('handles a null from_status without crashing, rendering only the to-status badge (AC1)', async () => {
    render(<ApprovalsPage />)

    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[1].component_id).closest('tr')
    expect(row).not.toBeNull()
    expect(within(row as HTMLElement).getByText('Down')).toBeInTheDocument()
    // No StatusBadge label rendered for the null from_status.
    expect(within(row as HTMLElement).queryByText('Unknown')).not.toBeInTheDocument()
  })

  it('renders the proposed_at timestamp in monospace (AC1)', async () => {
    render(<ApprovalsPage />)

    await screen.findByRole('table')

    const time = screen.getByText(FIXTURE_PROPOSALS[0].proposed_at)
    expect(time).toHaveClass('text-mono')
  })

  it('renders the empty state when there are no open proposals (AC1)', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))

    render(<ApprovalsPage />)

    expect(
      await screen.findByText('nothing pending approval'),
    ).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
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

    render(<ApprovalsPage />)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Could not load proposals',
    )

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await screen.findByRole('table')
    expect(callCount).toBe(2)
  })

  it('renders an Approve and a Reject action per open proposal (AC1, AC4)', async () => {
    render(<ApprovalsPage />)

    await screen.findByRole('table')

    for (const proposal of FIXTURE_PROPOSALS) {
      const row = screen.getByText(proposal.component_id).closest('tr')
      expect(row).not.toBeNull()
      expect(
        within(row as HTMLElement).getByRole('button', { name: 'Approve' }),
      ).toBeInTheDocument()
      expect(
        within(row as HTMLElement).getByRole('button', { name: 'Reject' }),
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

    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(target.component_id).closest('tr') as HTMLElement
    await user.click(within(row).getByRole('button', { name: 'Approve' }))

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

    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(target.component_id).closest('tr') as HTMLElement
    await user.click(within(row).getByRole('button', { name: 'Reject' }))

    await user.click(await screen.findByRole('button', { name: 'Confirm reject' }))

    await waitFor(() =>
      expect(screen.queryByText(target.component_id)).not.toBeInTheDocument(),
    )
    expect(postedBody).toEqual({ action: 'reject', actor: getActor() })
    expect(getCallCount).toBe(2)
  })

  it('lets the operator dismiss the confirmation step without POSTing (AC4)', async () => {
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

    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest(
      'tr',
    ) as HTMLElement
    await user.click(within(row).getByRole('button', { name: 'Approve' }))

    await user.click(await screen.findByRole('button', { name: 'Cancel' }))

    expect(screen.queryByRole('button', { name: 'Confirm approve' })).not.toBeInTheDocument()
    expect(within(row).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(postCalled).toBe(false)
  })

  it('is keyboard-operable: Enter on a focused Approve button opens the confirmation (AC4)', async () => {
    const user = userEvent.setup()
    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest(
      'tr',
    ) as HTMLElement
    const approveButton = within(row).getByRole('button', { name: 'Approve' })
    approveButton.focus()
    await user.keyboard('{Enter}')

    expect(await screen.findByRole('button', { name: 'Confirm approve' })).toBeInTheDocument()
  })

  it('shows an inline "already resolved" message and refreshes the list on a 409 lost race (AC3)', async () => {
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

    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest(
      'tr',
    ) as HTMLElement
    await user.click(within(row).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    expect(await screen.findByText(/already been resolved/i)).toBeInTheDocument()
    await waitFor(() => expect(getCallCount).toBe(2))
  })

  it('shows an inline "no longer exists" message and refreshes the list on a 404 (AC3)', async () => {
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

    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest(
      'tr',
    ) as HTMLElement
    await user.click(within(row).getByRole('button', { name: 'Reject' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm reject' }))

    expect(await screen.findByText(/no longer exists/i)).toBeInTheDocument()
    await waitFor(() => expect(getCallCount).toBe(2))
  })

  it('shows the shell ErrorState with retry on a generic decision failure, and retry re-attempts the POST (AC3)', async () => {
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

    render(<ApprovalsPage />)
    await screen.findByRole('table')

    const row = screen.getByText(FIXTURE_PROPOSALS[0].component_id).closest(
      'tr',
    ) as HTMLElement
    await user.click(within(row).getByRole('button', { name: 'Approve' }))
    await user.click(await screen.findByRole('button', { name: 'Confirm approve' }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await waitFor(() => expect(screen.queryByRole('alert')).not.toBeInTheDocument())
    // The list refresh (triggered by the successful retry) unmounts and
    // remounts the table, so re-locate the row instead of reusing the
    // pre-refresh reference.
    await screen.findByRole('table')
    const refreshedRow = screen
      .getByText(FIXTURE_PROPOSALS[0].component_id)
      .closest('tr') as HTMLElement
    expect(within(refreshedRow).getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(attempt).toBe(2)
  })
})
