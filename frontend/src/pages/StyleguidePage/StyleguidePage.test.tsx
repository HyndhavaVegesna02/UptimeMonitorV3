import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StyleguidePage } from './StyleguidePage'

describe('StyleguidePage', () => {
  it('renders a single top-level heading', () => {
    render(<StyleguidePage />)
    expect(screen.getByRole('heading', { name: 'Design system', level: 1 })).toBeInTheDocument()
  })

  it('renders every Button variant, including disabled and icon-only', () => {
    render(<StyleguidePage />)
    const section = screen.getByRole('region', { name: 'Button' })
    expect(within(section).getByRole('button', { name: 'Primary' })).toBeInTheDocument()
    expect(within(section).getByRole('button', { name: 'Secondary' })).toBeInTheDocument()
    expect(within(section).getByRole('button', { name: 'Ghost' })).toBeInTheDocument()
    expect(within(section).getByRole('button', { name: 'Disabled' })).toBeDisabled()
    expect(within(section).getByRole('button', { name: 'Search' })).toBeInTheDocument()
  })

  it('renders the Panel section, including the interactive (hover-lift) variant', () => {
    render(<StyleguidePage />)
    const section = screen.getByRole('region', { name: 'Panel' })
    expect(within(section).getByText('Static panel')).toBeInTheDocument()
    expect(within(section).getByText('Interactive panel')).toBeInTheDocument()
  })

  it('renders every StatusBadge health status', () => {
    render(<StyleguidePage />)
    const section = screen.getByRole('region', { name: 'StatusBadge' })
    for (const label of [
      'Up',
      'Degraded',
      'Partial outage',
      'Down',
      'Maintenance',
      'Unknown',
      'Missing data',
    ]) {
      expect(within(section).getByText(label)).toBeInTheDocument()
    }
  })

  it('renders SummaryCard variants, including the attention link card', () => {
    render(<StyleguidePage />)
    const section = screen.getByRole('region', { name: 'SummaryCard' })
    expect(within(section).getByText('Overall availability · 24h')).toBeInTheDocument()
    expect(within(section).getByRole('link', { name: /Pending approvals/ })).toBeInTheDocument()
  })

  it('renders a Sparkline sample', () => {
    render(<StyleguidePage />)
    const section = screen.getByRole('region', { name: 'Sparkline' })
    expect(section.querySelector('svg.sparkline')).not.toBeNull()
  })

  it('renders LoadingState, ErrorState (with and without retry), and EmptyState', () => {
    render(<StyleguidePage />)
    const section = screen.getByRole('region', { name: /Loading .* Empty/ })
    expect(within(section).getByRole('status')).toBeInTheDocument()
    expect(within(section).getAllByRole('alert').length).toBeGreaterThan(0)
    expect(within(section).getByRole('button', { name: 'Retry' })).toBeInTheDocument()
    expect(within(section).getByText('No components yet')).toBeInTheDocument()
  })

  describe('Loading/Error/Empty gallery alignment (STORY-141 AC3)', () => {
    // NOTE: this is a STRUCTURAL check only (necessary, not sufficient) —
    // jsdom does not compute layout, so it cannot itself PROVE the entries
    // render left-aligned. The actual visual left-alignment claim is
    // confirmed at the live reality gate.
    it('presents the demo row left-aligned, distinct from the Panel section\'s stretched stack', () => {
      render(<StyleguidePage />)
      const statesSection = screen.getByRole('region', { name: /Loading .* Empty/ })
      const statesRow = statesSection.querySelector('.styleguide-row')
      expect(statesRow).toHaveClass('styleguide-row--start')

      const panelSection = screen.getByRole('region', { name: 'Panel' })
      const panelRow = panelSection.querySelector('.styleguide-row')
      expect(panelRow).not.toHaveClass('styleguide-row--start')
      expect(panelRow).toHaveClass('styleguide-row--stack')
    })
  })
})
