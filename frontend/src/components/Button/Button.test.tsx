import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from './Button'

describe('Button (Mission Teal v2 — STORY-103: primary/ghost/danger + loading)', () => {
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

  it('applies the ghost variant class', () => {
    render(<Button variant="ghost">Cancel</Button>)
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveClass(
      'button--ghost',
    )
  })

  it('applies the danger variant class', () => {
    render(<Button variant="danger">Delete</Button>)
    expect(screen.getByRole('button', { name: 'Delete' })).toHaveClass(
      'button--danger',
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

  describe('loading state', () => {
    it('sets aria-busy and disables the button while loading', () => {
      render(<Button loading>Approve</Button>)
      const button = screen.getByRole('button', { name: 'Approve' })
      expect(button).toHaveAttribute('aria-busy', 'true')
      expect(button).toBeDisabled()
    })

    it('keeps the accessible name while loading (never loses its label)', () => {
      render(<Button loading>Approve</Button>)
      expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument()
    })

    it('renders a decorative loading spinner', () => {
      const { container } = render(<Button loading>Approve</Button>)
      const spinner = container.querySelector('.button__spinner')
      expect(spinner).not.toBeNull()
      expect(spinner).toHaveAttribute('aria-hidden', 'true')
    })

    it('does not fire onClick while loading', async () => {
      const user = userEvent.setup()
      const onClick = vi.fn()
      render(
        <Button onClick={onClick} loading>
          Approve
        </Button>,
      )

      await user.click(screen.getByRole('button', { name: 'Approve' }))

      expect(onClick).not.toHaveBeenCalled()
    })

    it('does not render the spinner when not loading', () => {
      const { container } = render(<Button>Approve</Button>)
      expect(container.querySelector('.button__spinner')).toBeNull()
      expect(screen.getByRole('button')).not.toHaveAttribute('aria-busy')
    })
  })
})
