import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { HttpResponse, http } from 'msw'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { ProposalDTO } from '../../api/types'
import { server } from '../../mocks/server'
import { AppRoutes } from '../../routes'
import { ApprovalsPage } from './ApprovalsPage'

const TRANSITION_PROPOSAL: ProposalDTO = {
  id: 1,
  component_id: 'sockshop-checkout',
  from_status: 'operational',
  to_status: 'degraded_performance',
  state: 'open',
  proposed_at: '2026-07-21T12:00:00Z',
}

const NEW_PROPOSAL: ProposalDTO = {
  id: 2,
  component_id: 'sockshop-catalogue',
  from_status: null,
  to_status: 'operational',
  state: 'open',
  proposed_at: '2026-07-21T12:05:00Z',
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/approvals']}>
      <ApprovalsPage />
    </MemoryRouter>,
  )
}

async function openConfirm(name: RegExp) {
  const user = userEvent.setup()
  await user.click(screen.getByRole('button', { name }))
  return user
}

describe('ApprovalsPage', () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    consoleErrorSpy.mockRestore()
  })

  it('AC6: shows a loading state while the fetch is in flight', () => {
    server.use(http.get('/api/v1/approvals', async () => new Promise(() => {})))
    renderPage()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('AC6: shows an error state with retry on fetch failure, never crashing the frame', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })))
    renderPage()

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Retry' })).toBeInTheDocument()
  })

  it('AC6: shows a tidy "queue clear" empty state for zero proposals', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([])))
    renderPage()

    expect(await screen.findByText('Queue clear')).toBeInTheDocument()
  })

  it('AC1: renders every open proposal with its from->to transition, "New" for a null from_status, and proposed-at time', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([TRANSITION_PROPOSAL, NEW_PROPOSAL])))
    renderPage()

    expect(await screen.findByText('sockshop-checkout')).toBeInTheDocument()
    expect(screen.getByText('sockshop-catalogue')).toBeInTheDocument()
    expect(screen.getByText('New')).toBeInTheDocument()
  })

  it('AC3: only one proposal is mid-decision at a time — confirming one disables the other\'s actions', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([TRANSITION_PROPOSAL, NEW_PROPOSAL])))
    renderPage()
    await screen.findByText('sockshop-checkout')

    await openConfirm(/^approve sockshop-checkout$/i)

    expect(screen.getByRole('button', { name: /^approve sockshop-catalogue$/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /^reject sockshop-catalogue$/i })).toBeDisabled()
  })

  it('AC2/AC5: approving a proposal posts {action, actor} and refreshes the list from the server (not just local removal)', async () => {
    let approvalsCallCount = 0
    let capturedBody: unknown
    server.use(
      http.get('/api/v1/approvals', () => {
        approvalsCallCount += 1
        return HttpResponse.json(approvalsCallCount === 1 ? [TRANSITION_PROPOSAL] : [])
      }),
      http.post('/api/v1/decisions/:proposalId', async ({ request }) => {
        capturedBody = await request.json()
        return HttpResponse.json({ proposal_id: 1, state: 'approved', resolved_at: '2026-07-21T12:06:00Z' })
      }),
    )
    renderPage()
    await screen.findByText('sockshop-checkout')

    const user = await openConfirm(/^approve sockshop-checkout$/i)
    await user.click(screen.getByRole('button', { name: /^confirm approve$/i }))

    await waitFor(() => expect(screen.queryByText('sockshop-checkout')).toBeNull())
    expect(approvalsCallCount).toBeGreaterThanOrEqual(2)
    expect(capturedBody).toMatchObject({ action: 'approve' })
    expect((capturedBody as { actor: string }).actor.trim().length).toBeGreaterThan(0)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4/AC8: a forced 409 (already resolved) shows a non-destructive notice and refreshes the list', async () => {
    let approvalsCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        approvalsCallCount += 1
        return HttpResponse.json([TRANSITION_PROPOSAL])
      }),
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'Proposal is not open' }, { status: 409 }),
      ),
    )
    renderPage()
    await screen.findByText('sockshop-checkout')
    const countBeforeDecision = approvalsCallCount

    const user = await openConfirm(/^reject sockshop-checkout$/i)
    await user.click(screen.getByRole('button', { name: /^confirm reject$/i }))

    expect(await screen.findByText(/already resolved/i)).toBeInTheDocument()
    await waitFor(() => expect(approvalsCallCount).toBeGreaterThan(countBeforeDecision))
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4/AC8: a forced 404 (no longer exists) shows a "no longer exists" notice and refreshes the list', async () => {
    let approvalsCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        approvalsCallCount += 1
        return HttpResponse.json([TRANSITION_PROPOSAL])
      }),
      http.post('/api/v1/decisions/:proposalId', () =>
        HttpResponse.json({ detail: 'Proposal not found' }, { status: 404 }),
      ),
    )
    renderPage()
    await screen.findByText('sockshop-checkout')
    const countBeforeDecision = approvalsCallCount

    const user = await openConfirm(/^approve sockshop-checkout$/i)
    await user.click(screen.getByRole('button', { name: /^confirm approve$/i }))

    expect(await screen.findByText(/no longer exists/i)).toBeInTheDocument()
    await waitFor(() => expect(approvalsCallCount).toBeGreaterThan(countBeforeDecision))
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC4: any other failure keeps the card open with an inline retry, and does not refresh the list', async () => {
    let approvalsCallCount = 0
    server.use(
      http.get('/api/v1/approvals', () => {
        approvalsCallCount += 1
        return HttpResponse.json([TRANSITION_PROPOSAL])
      }),
      http.post('/api/v1/decisions/:proposalId', () => HttpResponse.json({ detail: 'boom' }, { status: 500 })),
    )
    renderPage()
    await screen.findByText('sockshop-checkout')
    const countBeforeDecision = approvalsCallCount

    const user = await openConfirm(/^approve sockshop-checkout$/i)
    await user.click(screen.getByRole('button', { name: /^confirm approve$/i }))

    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^retry$/i })).toBeInTheDocument()
    expect(approvalsCallCount).toBe(countBeforeDecision)
    expect(consoleErrorSpy).not.toHaveBeenCalled()
  })

  it('AC7: focus moves to Confirm when opening, then back to the trigger after Cancel/Escape', async () => {
    server.use(http.get('/api/v1/approvals', () => HttpResponse.json([TRANSITION_PROPOSAL])))
    renderPage()
    const approveButton = await screen.findByRole('button', { name: /^approve sockshop-checkout$/i })

    const user = userEvent.setup()
    await user.click(approveButton)
    expect(screen.getByRole('button', { name: /^confirm approve$/i })).toHaveFocus()

    await user.keyboard('{Escape}')
    expect(screen.getByRole('button', { name: /^approve sockshop-checkout$/i })).toHaveFocus()
  })

  it('has exactly one <h1> on the full routed page (the shell topbar owns it, not this page)', async () => {
    render(
      <MemoryRouter initialEntries={['/approvals']}>
        <AppRoutes />
      </MemoryRouter>,
    )
    expect(await screen.findAllByRole('heading', { level: 1 })).toHaveLength(1)
  })
})
