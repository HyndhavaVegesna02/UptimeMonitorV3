import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { WindowToggle } from './WindowToggle'

describe('WindowToggle', () => {
  it('renders a labelled group with one button per window option, 24h/7d/30d in order', () => {
    render(<WindowToggle value="24h" onChange={vi.fn()} />)

    const group = screen.getByRole('group', { name: 'Window' })
    const buttons = screen.getAllByRole('button')
    expect(buttons.map((button) => button.textContent)).toEqual(['24h', '7d', '30d'])
    expect(group).toBeInTheDocument()
  })

  it('marks the current window aria-pressed=true and the others false', () => {
    render(<WindowToggle value="7d" onChange={vi.fn()} />)

    expect(screen.getByRole('button', { name: '24h' })).toHaveAttribute('aria-pressed', 'false')
    expect(screen.getByRole('button', { name: '7d' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByRole('button', { name: '30d' })).toHaveAttribute('aria-pressed', 'false')
  })

  it('calls onChange with the clicked window key', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<WindowToggle value="24h" onChange={onChange} />)

    await user.click(screen.getByRole('button', { name: '30d' }))

    expect(onChange).toHaveBeenCalledWith('30d')
  })

  it('is keyboard-operable (Enter activates a focused button)', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(<WindowToggle value="24h" onChange={onChange} />)

    await user.tab()
    await user.tab()
    expect(screen.getByRole('button', { name: '7d' })).toHaveFocus()
    await user.keyboard('{Enter}')

    expect(onChange).toHaveBeenCalledWith('7d')
  })
})
