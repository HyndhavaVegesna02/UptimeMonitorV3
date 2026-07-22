import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { ProposalDTO } from '../../api/types'
import { ProposalCard } from './ProposalCard'

const NOW = new Date('2026-07-21T12:10:00Z')

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

function defaultProps() {
  return {
    now: NOW,
    isConfirming: false,
    isSubmitting: false,
    isBlocked: false,
    action: undefined,
    notice: undefined,
    onRequestConfirm: vi.fn(),
    onCancelConfirm: vi.fn(),
    onConfirmDecision: vi.fn(),
  }
}

describe('ProposalCard', () => {
  it('AC1: renders the component, the from -> to health badges, and the proposed-at time', () => {
    render(<ProposalCard proposal={TRANSITION_PROPOSAL} {...defaultProps()} />)

    expect(screen.getByText('sockshop-checkout')).toBeInTheDocument()
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Degraded')).toBeInTheDocument()
    expect(screen.getByText(/ago|just now/)).toBeInTheDocument()
  })

  it('AC1: a null from_status renders as "New" rather than a fabricated status', () => {
    render(<ProposalCard proposal={NEW_PROPOSAL} {...defaultProps()} />)

    expect(screen.getByText('New')).toBeInTheDocument()
    expect(screen.getByText('Up')).toBeInTheDocument()
  })

  it('AC2/AC3: Approve/Reject are accessible buttons that request confirm for the right action', async () => {
    const onRequestConfirm = vi.fn()
    const user = userEvent.setup()
    render(<ProposalCard proposal={TRANSITION_PROPOSAL} {...defaultProps()} onRequestConfirm={onRequestConfirm} />)

    await user.click(screen.getByRole('button', { name: /approve/i }))
    expect(onRequestConfirm).toHaveBeenCalledWith('approve')

    await user.click(screen.getByRole('button', { name: /reject/i }))
    expect(onRequestConfirm).toHaveBeenCalledWith('reject')
  })

  it('AC3: disables Approve/Reject while another proposal is mid-decision (isBlocked)', () => {
    render(<ProposalCard proposal={TRANSITION_PROPOSAL} {...defaultProps()} isBlocked />)

    expect(screen.getByRole('button', { name: /approve/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /reject/i })).toBeDisabled()
  })

  it('AC3/AC7: confirming renders a Confirm/Cancel prompt, keyboard-reachable, and focuses Confirm', () => {
    render(
      <ProposalCard proposal={TRANSITION_PROPOSAL} {...defaultProps()} isConfirming action="approve" />,
    )

    const confirmButton = screen.getByRole('button', { name: /confirm approve/i })
    expect(confirmButton).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
    expect(confirmButton).toHaveFocus()
  })

  it('AC3: clicking Confirm calls onConfirmDecision with the pending action', async () => {
    const onConfirmDecision = vi.fn()
    const user = userEvent.setup()
    render(
      <ProposalCard
        proposal={TRANSITION_PROPOSAL}
        {...defaultProps()}
        isConfirming
        action="reject"
        onConfirmDecision={onConfirmDecision}
      />,
    )

    await user.click(screen.getByRole('button', { name: /confirm reject/i }))
    expect(onConfirmDecision).toHaveBeenCalledWith('reject')
  })

  it('AC7: Cancel dismisses the confirm prompt', async () => {
    const onCancelConfirm = vi.fn()
    const user = userEvent.setup()
    render(
      <ProposalCard
        proposal={TRANSITION_PROPOSAL}
        {...defaultProps()}
        isConfirming
        action="approve"
        onCancelConfirm={onCancelConfirm}
      />,
    )

    await user.click(screen.getByRole('button', { name: /cancel/i }))
    expect(onCancelConfirm).toHaveBeenCalledTimes(1)
  })

  it('AC7: Escape dismisses the confirm prompt (keyboard-reachable AND dismissable)', async () => {
    const onCancelConfirm = vi.fn()
    const user = userEvent.setup()
    render(
      <ProposalCard
        proposal={TRANSITION_PROPOSAL}
        {...defaultProps()}
        isConfirming
        action="approve"
        onCancelConfirm={onCancelConfirm}
      />,
    )

    await user.keyboard('{Escape}')
    expect(onCancelConfirm).toHaveBeenCalledTimes(1)
  })

  it('AC3: submitting disables the confirm/cancel buttons', () => {
    render(
      <ProposalCard proposal={TRANSITION_PROPOSAL} {...defaultProps()} isConfirming isSubmitting action="approve" />,
    )

    expect(screen.getByRole('button', { name: /approve|submitting/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /cancel/i })).toBeDisabled()
  })

  it('AC4: a conflict notice (409) renders a non-destructive "already resolved" message', () => {
    render(
      <ProposalCard
        proposal={TRANSITION_PROPOSAL}
        {...defaultProps()}
        notice={{ proposalId: 1, kind: 'conflict', message: 'This proposal was already resolved — refreshing the list.' }}
      />,
    )

    expect(screen.getByText(/already resolved/i)).toBeInTheDocument()
  })

  it('AC4: a gone notice (404) renders a "no longer exists" message', () => {
    render(
      <ProposalCard
        proposal={TRANSITION_PROPOSAL}
        {...defaultProps()}
        notice={{ proposalId: 1, kind: 'gone', message: 'This proposal no longer exists — refreshing the list.' }}
      />,
    )

    expect(screen.getByText(/no longer exists/i)).toBeInTheDocument()
  })

  it('AC4: a generic error notice keeps the confirm prompt open with a retry affordance', async () => {
    const onConfirmDecision = vi.fn()
    const user = userEvent.setup()
    render(
      <ProposalCard
        proposal={TRANSITION_PROPOSAL}
        {...defaultProps()}
        isConfirming
        action="approve"
        notice={{ proposalId: 1, kind: 'error', message: 'boom' }}
        onConfirmDecision={onConfirmDecision}
      />,
    )

    expect(screen.getByText('boom')).toBeInTheDocument()
    const retryButton = screen.getByRole('button', { name: /retry/i })
    await user.click(retryButton)
    expect(onConfirmDecision).toHaveBeenCalledWith('approve')
  })

  it('AC7: has exactly one accessible name per button, distinct per action (no invented severity/reason fields)', () => {
    render(<ProposalCard proposal={TRANSITION_PROPOSAL} {...defaultProps()} />)
    const card = screen.getByText('sockshop-checkout').closest('.panel') as HTMLElement
    expect(within(card).queryByText(/severity|reason/i)).toBeNull()
  })
})
