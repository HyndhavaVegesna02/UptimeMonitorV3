import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { RosterRow } from './deriveRoster'
import { ComponentsRoster } from './ComponentsRoster'

const ROWS: RosterRow[] = [
  {
    component: { id: 'http-check', name: 'HTTP Check', status: 'operational' },
    health: 'up',
    uptimePct: 1,
    latestLatencyMs: 588,
    latencyTrend: [951, 588],
  },
  {
    component: { id: 'no-data-yet', name: 'No Data Yet', status: 'operational' },
    health: 'up',
    uptimePct: null,
    latestLatencyMs: null,
    latencyTrend: [],
  },
]

describe('ComponentsRoster', () => {
  it('renders one row per component with status dot+label, uptime, and latest latency', () => {
    render(<ComponentsRoster rows={ROWS} />)
    expect(screen.getByText('HTTP Check')).toBeInTheDocument()
    expect(screen.getAllByText('Up')).toHaveLength(2)
    expect(screen.getByText(/100\.00/)).toBeInTheDocument()
    expect(screen.getByText(/588/)).toBeInTheDocument()
  })

  it('renders an em dash uptime for a component with no signal data yet', () => {
    render(<ComponentsRoster rows={ROWS} />)
    expect(screen.getAllByText(/—/).length).toBeGreaterThan(0)
  })

  it('renders an EmptyState when there are no components', () => {
    render(<ComponentsRoster rows={[]} />)
    expect(screen.getByText(/No components/)).toBeInTheDocument()
  })
})
