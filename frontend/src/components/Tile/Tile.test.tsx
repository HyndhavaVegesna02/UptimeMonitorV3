import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { Tile } from './Tile'

describe('Tile (bento card primitive — STORY-103)', () => {
  it('renders as a plain container (div) by default, non-interactive', () => {
    const { container } = render(<Tile>Hello</Tile>)
    const tile = container.querySelector('.tile')
    expect(tile).not.toBeNull()
    expect(tile?.tagName).toBe('DIV')
    expect(tile).not.toHaveClass('tile--interactive')
  })

  it('defaults to md elevation', () => {
    const { container } = render(<Tile>Hello</Tile>)
    expect(container.querySelector('.tile')).toHaveClass('tile--elevation-md')
  })

  it('applies the requested elevation level', () => {
    const { container } = render(<Tile elevation="lg">Hello</Tile>)
    expect(container.querySelector('.tile')).toHaveClass('tile--elevation-lg')
  })

  it('applies an optional status accent edge', () => {
    const { container } = render(<Tile accent="down">Hello</Tile>)
    expect(container.querySelector('.tile')).toHaveClass('tile--accent-down')
  })

  it('renders no accent class when accent is omitted', () => {
    const { container } = render(<Tile>Hello</Tile>)
    const classes = Array.from(container.querySelector('.tile')?.classList ?? [])
    expect(classes.some((c) => c.startsWith('tile--accent-'))).toBe(false)
  })

  it('renders as a react-router Link when href is given, auto-interactive', () => {
    render(
      <MemoryRouter>
        <Tile href="/dashboard">Go to dashboard</Tile>
      </MemoryRouter>,
    )
    const link = screen.getByRole('link', { name: 'Go to dashboard' })
    expect(link).toHaveAttribute('href', '/dashboard')
    expect(link).toHaveClass('tile', 'tile--interactive')
  })

  it('renders as a button when onClick is given (no href), auto-interactive', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(<Tile onClick={onClick}>Do the thing</Tile>)

    const button = screen.getByRole('button', { name: 'Do the thing' })
    expect(button).toHaveClass('tile--interactive')

    await user.click(button)
    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('is keyboard-activatable when interactive via onClick (native button semantics)', async () => {
    const user = userEvent.setup()
    const onClick = vi.fn()
    render(<Tile onClick={onClick}>Do the thing</Tile>)

    const button = screen.getByRole('button', { name: 'Do the thing' })
    button.focus()
    await user.keyboard('{Enter}')

    expect(onClick).toHaveBeenCalledTimes(1)
  })

  it('honors an explicit interactive=false even with an onClick (rare override)', () => {
    const { container } = render(
      <Tile onClick={() => {}} interactive={false}>
        Hello
      </Tile>,
    )
    // Still a button (onClick needs a real interactive element) but
    // without the hover/focus interactive AFFORDANCE class.
    expect(container.querySelector('.tile')).not.toHaveClass('tile--interactive')
  })

  it('passes through a className and other div attributes', () => {
    const { container } = render(
      <Tile className="extra" aria-label="Custom">
        Hello
      </Tile>,
    )
    const tile = container.querySelector('.tile')
    expect(tile).toHaveClass('extra')
    expect(tile).toHaveAttribute('aria-label', 'Custom')
  })
})
