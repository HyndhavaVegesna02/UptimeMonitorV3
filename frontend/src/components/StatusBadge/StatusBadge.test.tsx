import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusBadge } from './StatusBadge'

describe('StatusBadge', () => {
  it('renders a default label per health status', () => {
    render(<StatusBadge status="up" />)
    expect(screen.getByText('Up')).toBeInTheDocument()
  })

  it.each([
    ['up', 'Up'],
    ['degraded', 'Degraded'],
    ['partial', 'Partial outage'],
    ['down', 'Down'],
    ['maintenance', 'Maintenance'],
    ['unknown', 'Unknown'],
    ['missing', 'Missing data'],
  ] as const)('maps status "%s" to the default label "%s"', (status, label) => {
    render(<StatusBadge status={status} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })

  it('accepts a label override', () => {
    render(<StatusBadge status="degraded" label="Checkout Flow degraded" />)
    expect(screen.getByText('Checkout Flow degraded')).toBeInTheDocument()
  })

  it('never conveys status by color alone — the dot is decorative, the label is the accessible name', () => {
    const { container } = render(<StatusBadge status="down" />)
    const dot = container.querySelector('.status-badge__dot')
    expect(dot).toHaveAttribute('aria-hidden', 'true')
    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('applies the status modifier class', () => {
    const { container } = render(<StatusBadge status="maintenance" />)
    expect(container.firstElementChild).toHaveClass('status-badge--maintenance')
  })
})
