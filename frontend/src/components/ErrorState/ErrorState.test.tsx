import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ErrorState } from './ErrorState'

describe('ErrorState', () => {
  it('renders a default message when none is given', () => {
    render(<ErrorState onRetry={() => {}} />)
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong')
  })

  it('renders a custom message', () => {
    render(<ErrorState message="Could not load components" onRetry={() => {}} />)
    expect(screen.getByRole('alert')).toHaveTextContent(
      'Could not load components',
    )
  })

  it('calls onRetry when the retry button is clicked', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    render(<ErrorState onRetry={onRetry} />)

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('omits the retry button when onRetry is not provided', () => {
    render(<ErrorState />)
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  })
})
