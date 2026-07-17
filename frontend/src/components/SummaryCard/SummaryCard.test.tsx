import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
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

  describe('neutralAtZero (STORY-099 AC1, journal D4)', () => {
    it('overrides a "bad state" tone to neutral when the numeric value is exactly 0', () => {
      const { container } = render(
        <SummaryCard label="Down" value={0} tone="down" neutralAtZero />,
      )
      expect(container.querySelector('.summary-card--down')).toBeNull()
      expect(container.querySelector('.summary-card--neutral')).not.toBeNull()
    })

    it('restores the status tone once the numeric value is above 0', () => {
      const { container } = render(
        <SummaryCard label="Down" value={2} tone="down" neutralAtZero />,
      )
      expect(container.querySelector('.summary-card--down')).not.toBeNull()
      expect(container.querySelector('.summary-card--neutral')).toBeNull()
    })

    it('does the same for degraded and partial tones at 0', () => {
      const { container: degraded } = render(
        <SummaryCard label="Degraded" value={0} tone="degraded" neutralAtZero />,
      )
      expect(degraded.querySelector('.summary-card--degraded')).toBeNull()
      expect(degraded.querySelector('.summary-card--neutral')).not.toBeNull()

      const { container: partial } = render(
        <SummaryCard label="Partial outage" value={0} tone="partial" neutralAtZero />,
      )
      expect(partial.querySelector('.summary-card--partial')).toBeNull()
      expect(partial.querySelector('.summary-card--neutral')).not.toBeNull()
    })

    it('never neutralizes a tone when neutralAtZero is not set, even at 0 (default behavior unchanged)', () => {
      const { container } = render(<SummaryCard label="Down" value={0} tone="down" />)
      expect(container.querySelector('.summary-card--down')).not.toBeNull()
    })

    it('leaves the "up" (Operational) tone green regardless of the count, by call-site convention (neutralAtZero simply unused there)', () => {
      const { container } = render(<SummaryCard label="Operational" value={0} tone="up" />)
      expect(container.querySelector('.summary-card--up')).not.toBeNull()
      expect(container.querySelector('.summary-card--neutral')).toBeNull()
    })

    it('only kicks in for a numeric 0 — a non-numeric value (e.g. a formatted string) keeps its tone', () => {
      const { container } = render(
        <SummaryCard label="Uptime" value="0.00%" tone="down" neutralAtZero />,
      )
      expect(container.querySelector('.summary-card--down')).not.toBeNull()
    })
  })

  describe('href (STORY-099 AC2 — whole-card interactive action cards)', () => {
    it('renders as a single focusable link wrapping the whole card when href is given', () => {
      render(
        <MemoryRouter>
          <SummaryCard label="Pending approvals" value={3} tone="accent" href="/approvals" />
        </MemoryRouter>,
      )
      const link = screen.getByRole('link', { name: /Pending approvals/ })
      expect(link).toHaveAttribute('href', '/approvals')
      expect(link).toHaveClass('summary-card', 'summary-card--accent', 'summary-card--interactive')
      // The label/value text lives INSIDE the single link element (one
      // interactive element for the whole card, not a nested control).
      expect(link.querySelector('.summary-card__value')).toHaveTextContent('3')
    })

    it('renders as a plain (non-interactive) div when href is omitted, as before', () => {
      const { container } = render(<SummaryCard label="Operational" value={1} tone="up" />)
      expect(screen.queryByRole('link')).not.toBeInTheDocument()
      expect(container.querySelector('.summary-card--interactive')).toBeNull()
    })
  })
})
