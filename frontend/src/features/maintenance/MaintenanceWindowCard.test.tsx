import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { MaintenanceWindowDTO } from '../../api/types'
import { MaintenanceWindowCard } from './MaintenanceWindowCard'

const NOW = new Date('2026-07-22T01:00:00Z')

const ACTIVE_WINDOW: MaintenanceWindowDTO = {
  id: 1,
  component_id: 'http-check',
  starts_at: '2026-07-22T00:00:00Z',
  ends_at: '2026-07-22T02:00:00Z',
  reason: 'DB upgrade',
  title: 'Planned DB maintenance',
}

function baseProps() {
  return {
    window: ACTIVE_WINDOW,
    now: NOW,
    isConfirming: false,
    isSubmitting: false,
    isBlocked: false,
    notice: undefined,
    onRequestConfirm: vi.fn(),
    onCancelConfirm: vi.fn(),
    onConfirmDelete: vi.fn(),
  }
}

describe('MaintenanceWindowCard', () => {
  it('AC1: renders title, component, range, and reason', () => {
    render(<MaintenanceWindowCard {...baseProps()} />)
    expect(screen.getByText('Planned DB maintenance')).toBeInTheDocument()
    expect(screen.getByText('http-check')).toBeInTheDocument()
    expect(screen.getByText('Jul 22 · 00:00–02:00 UTC')).toBeInTheDocument()
    expect(screen.getByText('DB upgrade')).toBeInTheDocument()
  })

  it('AC1: a null title falls back to a tidy default, and a null reason renders "—"', () => {
    render(
      <MaintenanceWindowCard
        {...baseProps()}
        window={{ ...ACTIVE_WINDOW, title: null, reason: null }}
      />,
    )
    expect(screen.getByText('Maintenance window')).toBeInTheDocument()
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('AC1: derives and shows the correct state badge from starts_at/ends_at vs now', () => {
    render(<MaintenanceWindowCard {...baseProps()} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('AC4: clicking Delete requests a confirm', async () => {
    const onRequestConfirm = vi.fn()
    const user = userEvent.setup()
    render(<MaintenanceWindowCard {...baseProps()} onRequestConfirm={onRequestConfirm} />)

    await user.click(screen.getByRole('button', { name: /delete/i }))

    expect(onRequestConfirm).toHaveBeenCalledTimes(1)
  })

  it('AC4: while confirming, shows a Confirm/Cancel pair; confirming calls onConfirmDelete', async () => {
    const onConfirmDelete = vi.fn()
    const user = userEvent.setup()
    render(<MaintenanceWindowCard {...baseProps()} isConfirming onConfirmDelete={onConfirmDelete} />)

    await user.click(screen.getByRole('button', { name: /^confirm delete$/i }))

    expect(onConfirmDelete).toHaveBeenCalledTimes(1)
  })

  it('AC4: Cancel calls onCancelConfirm', async () => {
    const onCancelConfirm = vi.fn()
    const user = userEvent.setup()
    render(<MaintenanceWindowCard {...baseProps()} isConfirming onCancelConfirm={onCancelConfirm} />)

    await user.click(screen.getByRole('button', { name: /^cancel$/i }))

    expect(onCancelConfirm).toHaveBeenCalledTimes(1)
  })

  it('AC4: isBlocked disables the delete action', () => {
    render(<MaintenanceWindowCard {...baseProps()} isBlocked />)
    expect(screen.getByRole('button', { name: /delete/i })).toBeDisabled()
  })

  it('AC4: a "gone" notice renders as a non-destructive status message', () => {
    render(
      <MaintenanceWindowCard
        {...baseProps()}
        notice={{ windowId: 1, kind: 'gone', message: 'This window was already deleted — refreshing the list.' }}
      />,
    )
    expect(screen.getByRole('status')).toHaveTextContent(/already deleted/i)
  })

  it('AC4: an "error" notice renders as an alert while confirming', () => {
    render(
      <MaintenanceWindowCard
        {...baseProps()}
        isConfirming
        notice={{ windowId: 1, kind: 'error', message: 'boom' }}
      />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('boom')
  })
})
