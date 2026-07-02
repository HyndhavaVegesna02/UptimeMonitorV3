import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { server } from '../mocks/server'
import { FIXTURE_PROPOSALS } from '../mocks/handlers'
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
})
