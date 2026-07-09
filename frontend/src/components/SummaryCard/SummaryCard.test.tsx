import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SummaryCard } from './SummaryCard'

describe('SummaryCard', () => {
  it('renders the label, value, and sub text', () => {
    render(<SummaryCard label="Operational" value={12} sub="of 14 components" />)
    expect(screen.getByText('Operational')).toBeInTheDocument()
    expect(screen.getByText('12')).toBeInTheDocument()
    expect(screen.getByText('of 14 components')).toBeInTheDocument()
  })

  it('renders without a sub line when none is given', () => {
    render(<SummaryCard label="Open proposals" value={0} />)
    expect(screen.getByText('Open proposals')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('renders a decorative status dot alongside the visible label/value text (never color-only)', () => {
    const { container } = render(
      <SummaryCard label="Outages" value={2} tone="down" />,
    )
    const dot = container.querySelector('.summary-card__dot')
    expect(dot).not.toBeNull()
    expect(dot).toHaveAttribute('aria-hidden', 'true')
    expect(screen.getByText('Outages')).toBeInTheDocument()
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('applies the tone modifier class driving the token-based color', () => {
    const { container: containerOk } = render(<SummaryCard label="30d uptime" value="99.98%" tone="ok" />)
    expect(containerOk.querySelector('.summary-card--ok')).not.toBeNull()

    const { container: containerUp } = render(<SummaryCard label="30d uptime" value="99.98%" tone="up" />)
    expect(containerUp.querySelector('.summary-card--up')).not.toBeNull()
  })

  it('defaults to the neutral tone when none is given', () => {
    const { container } = render(<SummaryCard label="Open proposals" value={3} />)
    expect(container.querySelector('.summary-card--neutral')).not.toBeNull()
  })
})
