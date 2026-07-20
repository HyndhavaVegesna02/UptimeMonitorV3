import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button } from './Button'

const buttonCss = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), 'Button.css'),
  'utf-8',
)

describe('Button', () => {
  it('renders its label', () => {
    render(<Button>Approve</Button>)
    expect(screen.getByRole('button', { name: 'Approve' })).toBeInTheDocument()
  })

  it('defaults to type="button" so it never submits a surrounding form', () => {
    render(<Button>Approve</Button>)
    expect(screen.getByRole('button', { name: 'Approve' })).toHaveAttribute('type', 'button')
  })

  it('defaults to the primary variant', () => {
    render(<Button>Approve</Button>)
    expect(screen.getByRole('button', { name: 'Approve' })).toHaveClass('button--primary')
  })

  it('applies the secondary variant class', () => {
    render(<Button variant="secondary">Cancel</Button>)
    expect(screen.getByRole('button', { name: 'Cancel' })).toHaveClass('button--secondary')
  })

  it('applies the ghost variant class', () => {
    render(<Button variant="ghost">Skip</Button>)
    expect(screen.getByRole('button', { name: 'Skip' })).toHaveClass('button--ghost')
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

  it('requires an accessible label for icon-only usage (aria-label)', () => {
    render(
      <Button iconOnly aria-label="Search">
        {null}
      </Button>,
    )
    expect(screen.getByRole('button', { name: 'Search' })).toHaveClass('button--icon-only')
  })

  it('declares hover/active/focus-visible affordances (emil + web-guidelines)', () => {
    expect(buttonCss).toMatch(/\.button(--[\w-]+)?:hover/)
    expect(buttonCss).toMatch(/\.button:active/)
    expect(buttonCss).toMatch(/\.button:focus-visible/)
  })

  it('press feedback animates only transform, guarded by prefers-reduced-motion', () => {
    expect(buttonCss).toMatch(/@media \(prefers-reduced-motion: no-preference\)/)
    expect(buttonCss).not.toMatch(/transition:\s*all/)
  })
})
