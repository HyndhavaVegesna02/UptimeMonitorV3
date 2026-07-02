import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it('renders its label', () => {
    render(<Button>Approve</Button>)
    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument()
  })

  it('defaults to type="button" so it never submits a surrounding form', () => {
    render(<Button>Approve</Button>)
    expect(screen.getByRole('button', { name: 'Approve' })).toHaveAttribute(
      'type',
      'button',
    )
  })

  it('defaults to the primary variant', () => {
    render(<Button>Approve</Button>)
    expect(screen.getByRole('button', { name: 'Approve' })).toHaveClass(
      'button--primary',
    )
  })

  it('applies the secondary variant class', () => {
    render(<Button variant="secondary">Cancel</Button>)
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveClass(
      'button--secondary',
    )
  })

  it('applies the tertiary variant class', () => {
    render(<Button variant="tertiary">Skip</Button>)
    expect(screen.getByRole('button', { name: 'Skip' })).toHaveClass(
      'button--tertiary',
    )
  })

  it('fires onClick when clicked', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Approve</Button>)

    await user.click(screen.getByRole('button', { name: 'Approve' }))

    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('does not fire onClick when disabled', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(
      <Button onClick={onClick} disabled>
        Approve
      </Button>,
    )

    await user.click(screen.getByRole('button', { name: 'Approve' }))

    expect(onClick).not.toHaveBeenCalled()
  })
})
