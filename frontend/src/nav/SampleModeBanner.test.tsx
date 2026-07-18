import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { SampleModeBanner } from './SampleModeBanner'

describe('SampleModeBanner', () => {
  it('renders nothing when not visible', () => {
    render(<SampleModeBanner visible={false} dismissed={false} onDismiss={vi.fn()} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('renders nothing when dismissed, even while visible', () => {
    render(<SampleModeBanner visible={true} dismissed={true} onDismiss={vi.fn()} />)
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('renders the warning as a live region when visible and not dismissed (role preserved, AC3)', () => {
    render(<SampleModeBanner visible={true} dismissed={false} onDismiss={vi.fn()} />)
    expect(
      screen.getByText(/sample mode — signals recorded as down/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('calls onDismiss when the Dismiss button is clicked (dismissal itself is controlled by the caller)', async () => {
    const user = userEvent.setup()
    const onDismiss = vi.fn()
    render(<SampleModeBanner visible={true} dismissed={false} onDismiss={onDismiss} />)

    await user.click(screen.getByRole('button', { name: 'Dismiss' }))

    expect(onDismiss).toHaveBeenCalledTimes(1)
  })
})
