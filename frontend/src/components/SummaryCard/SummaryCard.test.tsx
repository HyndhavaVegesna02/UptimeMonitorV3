import { ArrowUpRight } from '@phosphor-icons/react'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { SummaryCard } from './SummaryCard'

const summaryCardCss = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), 'SummaryCard.css'),
  'utf-8',
)

describe('SummaryCard', () => {
  it('renders the label, value, and unit', () => {
    render(<SummaryCard icon={ArrowUpRight} label="Overall availability · 24h" value="99.87" unit="%" />)
    expect(screen.getByText('Overall availability · 24h')).toBeInTheDocument()
    expect(screen.getByText('99.87')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()
  })

  it('renders an optional sub line', () => {
    render(
      <SummaryCard
        icon={ArrowUpRight}
        label="Components healthy"
        value="4/6"
        sub="1 degraded · 1 in maintenance"
      />,
    )
    expect(screen.getByText('1 degraded · 1 in maintenance')).toBeInTheDocument()
  })

  it('renders a delta pill with the given sentiment class', () => {
    render(
      <SummaryCard
        icon={ArrowUpRight}
        label="Avg response time"
        value="428"
        unit="ms"
        delta={{ text: '6.2%', sentiment: 'positive' }}
      />,
    )
    const delta = screen.getByText('6.2%')
    expect(delta.closest('.summary-card__delta')).toHaveClass('summary-card__delta--positive')
  })

  it('renders as a plain container by default (not a link)', () => {
    render(<SummaryCard icon={ArrowUpRight} label="Pending approvals" value="1" />)
    expect(screen.queryByRole('link')).toBeNull()
  })

  it('renders as a whole-card link when href is given, with attention styling', () => {
    render(
      <SummaryCard
        icon={ArrowUpRight}
        label="Pending approvals"
        value="1"
        href="/approvals"
        attention
      />,
    )
    const link = screen.getByRole('link', { name: /Pending approvals/ })
    expect(link).toHaveAttribute('href', '/approvals')
    expect(link).toHaveClass('summary-card--attention')
  })

  it('renders an optional extra slot (e.g. a sparkline) below the value', () => {
    render(
      <SummaryCard icon={ArrowUpRight} label="Overall availability" value="99.87" unit="%">
        <div data-testid="extra-slot">sparkline goes here</div>
      </SummaryCard>,
    )
    expect(screen.getByTestId('extra-slot')).toBeInTheDocument()
  })

  it('renders a compact EmptyState in place of the value/unit/sub block when `empty` is given (STORY-140 AC1)', () => {
    render(
      <SummaryCard
        icon={ArrowUpRight}
        label="Overall availability · 24h"
        value="—"
        unit="%"
        sub="Across 0 probe locations"
        empty={{ message: 'No data yet' }}
      />,
    )
    expect(screen.getByText('No data yet')).toBeInTheDocument()
    expect(screen.queryByText('—')).toBeNull()
    expect(screen.queryByText('Across 0 probe locations')).toBeNull()
    expect(screen.queryByText('%')).toBeNull()
  })

  it('passes an optional detail through to the empty treatment', () => {
    render(
      <SummaryCard
        icon={ArrowUpRight}
        label="Avg response time · 24h"
        value="—"
        unit="ms"
        empty={{ message: 'No data yet', detail: 'Checks will appear here once probes report in.' }}
      />,
    )
    expect(screen.getByText('Checks will appear here once probes report in.')).toBeInTheDocument()
  })

  it('declares hover/active/focus-visible affordances, guarded by prefers-reduced-motion', () => {
    expect(summaryCardCss).toMatch(/\.summary-card(--[\w-]+)?:hover/)
    expect(summaryCardCss).toMatch(/:focus-visible/)
    expect(summaryCardCss).toMatch(/@media \(prefers-reduced-motion: no-preference\)/)
    expect(summaryCardCss).not.toMatch(/transition:\s*all/)
  })
})
