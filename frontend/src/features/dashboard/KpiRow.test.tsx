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

  it('renders a clean "No data yet" treatment when availability_pct is null (degenerate window) — never a bare "— %" + "Across 0 probe locations" (STORY-140 AC1)', () => {
    render(<KpiRow {...DEFAULT_PROPS} availabilityPct={null} distinctLocations={0} />)
    const availabilityCard = screen.getByText('Overall availability · 24h').closest('article, a')!
    expect(within(availabilityCard as HTMLElement).getByText('No data yet')).toBeInTheDocument()
    expect(within(availabilityCard as HTMLElement).queryByText('—')).toBeNull()
    expect(within(availabilityCard as HTMLElement).queryByText(/Across 0 probe locations/)).toBeNull()
  })

  it('renders the avg response time KPI in ms', () => {
    render(<KpiRow {...DEFAULT_PROPS} />)
    expect(screen.getByText('Avg response time · 24h')).toBeInTheDocument()
    expect(screen.getByText('553')).toBeInTheDocument()
  })

  it('renders a clean "No data yet" treatment when avg_latency_ms is null (degenerate window) — consistent with the availability KPI (STORY-140 AC1)', () => {
    render(<KpiRow {...DEFAULT_PROPS} avgLatencyMs={null} />)
    const latencyCard = screen.getByText('Avg response time · 24h').closest('article, a')!
    expect(within(latencyCard as HTMLElement).getByText('No data yet')).toBeInTheDocument()
    expect(within(latencyCard as HTMLElement).queryByText('—')).toBeNull()
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

  it('gives every one of the 4 KPI cards a footer visual — none left with a visibly empty footprint vs its siblings (STORY-138 AC3)', () => {
    const { container } = render(<KpiRow {...DEFAULT_PROPS} />)
    expect(container.querySelectorAll('.summary-card__extra')).toHaveLength(4)
  })

  it('accents "Components healthy" by rule — negative when unhealthy, positive when all up (STORY-138 AC4)', () => {
    const { container, rerender } = render(
      <KpiRow {...DEFAULT_PROPS} componentsHealthy={2} componentsTotal={3} />,
    )
    expect(container.querySelector('.kpi-meter__fill--negative')).toBeInTheDocument()

    rerender(<KpiRow {...DEFAULT_PROPS} componentsHealthy={3} componentsTotal={3} />)
    expect(container.querySelector('.kpi-meter__fill--positive')).toBeInTheDocument()
  })

  it('accents "Pending approvals" by rule — accent when something is pending, neutral when the queue is empty (STORY-138 AC4)', () => {
    const { container, rerender } = render(<KpiRow {...DEFAULT_PROPS} pendingApprovals={0} />)
    expect(container.querySelector('.kpi-meter__fill--neutral')).toBeInTheDocument()

    rerender(<KpiRow {...DEFAULT_PROPS} pendingApprovals={3} />)
    expect(container.querySelector('.kpi-meter__fill--accent')).toBeInTheDocument()
  })
})
