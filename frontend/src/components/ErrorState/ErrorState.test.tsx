import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ErrorState } from './ErrorState'

describe('ErrorState', () => {
  it('announces via role="alert" with a default message', () => {
    render(<ErrorState />)
    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong')
  })

  it('accepts a custom message', () => {
    render(<ErrorState message="Could not load components" />)
    expect(screen.getByRole('alert')).toHaveTextContent('Could not load components')
  })

  it('renders no retry button when onRetry is omitted', () => {
    render(<ErrorState />)
    expect(screen.queryByRole('button')).toBeNull()
  })

  it('renders and fires a retry button when onRetry is given', async () => {
    const user = userEvent.setup()
    const onRetry = vi.fn()
    render(<ErrorState onRetry={onRetry} />)

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    expect(onRetry).toHaveBeenCalledTimes(1)
  })

  it('marks the warning icon as decorative — the text carries the message, not color/icon alone', () => {
    const { container } = render(<ErrorState />)
    expect(container.querySelector('.error-state__icon')).toHaveAttribute('aria-hidden', 'true')
  })
})
