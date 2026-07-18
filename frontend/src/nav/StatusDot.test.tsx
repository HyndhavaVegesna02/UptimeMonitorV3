import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { StatusDot } from './StatusDot'

describe('StatusDot', () => {
  it('carries an accessible name naming the state (never color alone, AC2)', () => {
    render(<StatusDot status="down" />)
    expect(screen.getByText('Overall status: Down')).toBeInTheDocument()
  })

  it('renders a decorative dot alongside the sr-only text', () => {
    const { container } = render(<StatusDot status="degraded" />)
    const dot = container.querySelector('.status-dot__mark')
    expect(dot).not.toBeNull()
    expect(dot).toHaveAttribute('aria-hidden', 'true')
    expect(dot).toHaveClass('status-dot__mark--degraded')
  })

  it('names every health status correctly', () => {
    const cases: Array<[Parameters<typeof StatusDot>[0]['status'], string]> = [
      ['up', 'Up'],
      ['degraded', 'Degraded'],
      ['partial', 'Partial outage'],
      ['down', 'Down'],
      ['maintenance', 'Maintenance'],
      ['unknown', 'Unknown'],
      ['missing', 'Missing data'],
    ]
    for (const [status, label] of cases) {
      const { unmount } = render(<StatusDot status={status} />)
      expect(screen.getByText(`Overall status: ${label}`)).toBeInTheDocument()
      unmount()
    }
  })

  it('renders as "Unknown" while the status is not yet loaded (undefined)', () => {
    render(<StatusDot status={undefined} />)
    expect(screen.getByText('Overall status: Unknown')).toBeInTheDocument()
  })
})
