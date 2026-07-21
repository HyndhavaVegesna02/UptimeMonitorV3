import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/approvals']}>
      <AppRoutes />
    </MemoryRouter>,
  )
}

describe('ApprovalsPage (STORY-131)', () => {
  it('renders heading and pending proposals list', async () => {
    renderPage()

    expect(screen.getByRole('heading', { level: 1, name: 'Approvals' })).toBeInTheDocument()

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Reject' })).toBeInTheDocument()
  })

  it('completes two-step confirmation flow for approving a proposal', async () => {
    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument()
    })

    const approveBtn = screen.getByRole('button', { name: 'Approve' })
    await user.click(approveBtn)

    expect(screen.getByText('Confirm approving this status transition?')).toBeInTheDocument()
    const confirmBtn = screen.getByRole('button', { name: 'Confirm Approve' })
    await user.click(confirmBtn)

    await waitFor(() => {
      expect(screen.getByRole('heading', { level: 1, name: 'Approvals' })).toBeInTheDocument()
    })
  })

  it('handles 409 ProposalNotOpenError with non-destructive inline warning (mandatory forced 409 test)', async () => {
    server.use(
      http.post('/api/v1/decisions/:proposalId', () => {
        return HttpResponse.json(
          { detail: 'Proposal 1 is not in open state' },
          { status: 409 },
        )
      }),
    )

    const user = userEvent.setup()
    renderPage()

    await waitFor(() => {
      expect(screen.getByText('#1')).toBeInTheDocument()
    })

    const approveBtn = screen.getByRole('button', { name: 'Approve' })
    await user.click(approveBtn)

    const confirmBtn = screen.getByRole('button', { name: 'Confirm Approve' })
    await user.click(confirmBtn)

    await waitFor(() => {
      expect(
        screen.getByText('This proposal has already been resolved or closed.'),
      ).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: 'Refresh List' })).toBeInTheDocument()
  })
})
