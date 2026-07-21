import { render, screen, within } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { KpiRow } from './KpiRow'

const kpiRowCss = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), 'KpiRow.css'), 'utf-8')

const DEFAULT_PROPS = {
  availabilityPct: 1.0,
  availabilityTrend: [1, 1, 0, 1],
  distinctLocations: 2,
  avgLatencyMs: 553,
  latencyTrend: [588, 951, 293],
  componentsHealthy: 1,
  componentsTotal: 1,
  componentsBreakdown: null,
  pendingApprovals: 0,
}

describe('KpiRow', () => {
  it('renders the overall availability KPI derived from the real availability_pct fraction', () => {
    render(<KpiRow {...DEFAULT_PROPS} />)
    expect(screen.getByText('Overall availability · 24h')).toBeInTheDocument()
    expect(screen.getByText('100.00')).toBeInTheDocument()
  })

  it('renders an em dash when availability_pct is null (degenerate window) rather than a fabricated number', () => {
    render(<KpiRow {...DEFAULT_PROPS} availabilityPct={null} />)
    const availabilityCard = screen.getByText('Overall availability · 24h').closest('article, a')!
    expect(within(availabilityCard as HTMLElement).getByText('—')).toBeInTheDocument()
  })

  it('renders the avg response time KPI in ms', () => {
    render(<KpiRow {...DEFAULT_PROPS} />)
    expect(screen.getByText('Avg response time · 24h')).toBeInTheDocument()
    expect(screen.getByText('553')).toBeInTheDocument()
  })

  it('renders components healthy as n/total with the real breakdown as a sub-line', () => {
    render(<KpiRow {...DEFAULT_PROPS} componentsHealthy={1} componentsTotal={4} componentsBreakdown="1 degraded · 2 in maintenance" />)
    expect(screen.getByText('Components healthy')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.getByText('/ 4')).toBeInTheDocument()
    expect(screen.getByText('1 degraded · 2 in maintenance')).toBeInTheDocument()
  })

  it('renders pending approvals as a card that links to /approvals', () => {
    render(<KpiRow {...DEFAULT_PROPS} pendingApprovals={2} />)
    const link = screen.getByRole('link', { name: /Pending approvals/ })
    expect(link).toHaveAttribute('href', '/approvals')
    expect(within(link).getByText('2')).toBeInTheDocument()
  })

  it('applies attention styling to the pending-approvals card only when count > 0', () => {
    const { rerender } = render(<KpiRow {...DEFAULT_PROPS} pendingApprovals={0} />)
    expect(screen.getByRole('link', { name: /Pending approvals/ })).not.toHaveClass(
      'summary-card--attention',
    )

    rerender(<KpiRow {...DEFAULT_PROPS} pendingApprovals={1} />)
    expect(screen.getByRole('link', { name: /Pending approvals/ })).toHaveClass(
      'summary-card--attention',
    )
  })

  it('never fabricates a delta pill (no real prior-period baseline is fetched)', () => {
    const { container } = render(<KpiRow {...DEFAULT_PROPS} />)
    expect(container.querySelector('.summary-card__delta')).toBeNull()
  })

  it('renders the section as a labelled landmark for the 4 KPI cards', () => {
    render(<KpiRow {...DEFAULT_PROPS} />)
    const section = screen.getByRole('region', { name: 'Key metrics' })
    expect(within(section).getAllByRole('article').length + within(section).getAllByRole('link').length).toBe(4)
  })

  it('lays out 4 KPI cards in a responsive grid, never `transition: all`', () => {
    expect(kpiRowCss).toMatch(/grid-template-columns/)
    expect(kpiRowCss).not.toMatch(/transition:\s*all\b/)
  })

  it('applies the shared entrance-stagger utility class to the KPI grid', () => {
    render(<KpiRow {...DEFAULT_PROPS} />)
    expect(screen.getByRole('region', { name: 'Key metrics' })).toHaveClass('stagger')
  })
})
