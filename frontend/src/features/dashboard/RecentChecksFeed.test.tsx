import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import type { RecentCheckRow } from './deriveRecentChecks'
import { RecentChecksFeed } from './RecentChecksFeed'

const ROWS: RecentCheckRow[] = [
  { key: '1', componentName: 'HTTP Check', locationLabel: '…0047', relativeTime: '28s ago', latencyMs: 294, health: 'up' },
  { key: '2', componentName: 'HTTP Check', locationLabel: '…0060', relativeTime: '1 min ago', latencyMs: null, health: 'down' },
]

describe('RecentChecksFeed', () => {
  it('renders one row per recent check with component, location, relative time, latency, and health tag', () => {
    render(<RecentChecksFeed rows={ROWS} />)
    expect(screen.getAllByText('HTTP Check')).toHaveLength(2)
    expect(screen.getByText(/…0047/)).toBeInTheDocument()
    expect(screen.getByText(/28s ago/)).toBeInTheDocument()
    expect(screen.getByText('294')).toBeInTheDocument()
    expect(screen.getByText('Up')).toBeInTheDocument()
    expect(screen.getByText('Down')).toBeInTheDocument()
  })

  it('renders an em dash for a null latency rather than a fabricated 0', () => {
    render(<RecentChecksFeed rows={ROWS} />)
    expect(screen.getByText('—')).toBeInTheDocument()
  })

  it('renders an EmptyState when there are no recent checks', () => {
    render(<RecentChecksFeed rows={[]} />)
    expect(screen.getByText(/No recent checks/)).toBeInTheDocument()
  })
})
