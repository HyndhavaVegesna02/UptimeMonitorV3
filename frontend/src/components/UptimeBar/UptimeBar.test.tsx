import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { UptimeBar } from './UptimeBar'

describe('UptimeBar', () => {
  it('renders one segment per entry, each with its per-segment tooltip title', () => {
    const { container } = render(
      <UptimeBar
        segments={[
          { status: 'up', title: 'Jul 01 — up' },
          { status: 'down', title: 'Jul 02 — down' },
          { status: 'degraded', title: 'Jul 03 — degraded' },
        ]}
      />,
    )
    const segments = container.querySelectorAll('.uptime-bar__segment')
    expect(segments).toHaveLength(3)
    expect(segments[0]).toHaveAttribute('title', 'Jul 01 — up')
    expect(segments[1]).toHaveAttribute('title', 'Jul 02 — down')
    expect(segments[2]).toHaveAttribute('title', 'Jul 03 — degraded')
  })

  it('colors each segment by its status via a modifier class', () => {
    const { container } = render(
      <UptimeBar
        segments={[
          { status: 'up', title: 'up' },
          { status: 'partial', title: 'partial' },
          { status: 'missing', title: 'missing' },
        ]}
      />,
    )
    expect(container.querySelector('.uptime-bar__segment--up')).not.toBeNull()
    expect(container.querySelector('.uptime-bar__segment--partial')).not.toBeNull()
    expect(container.querySelector('.uptime-bar__segment--missing')).not.toBeNull()
  })

  it('renders an accessible label for the whole bar', () => {
    render(
      <UptimeBar
        label="30-day uptime"
        segments={[{ status: 'up', title: 'up' }]}
      />,
    )
    expect(screen.getByRole('img', { name: '30-day uptime' })).toBeInTheDocument()
  })

  it('renders an explicit no-data state instead of a fabricated empty bar', () => {
    render(<UptimeBar segments={[]} label="30-day uptime" />)
    expect(screen.getByText('No data')).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: '30-day uptime: no data' }),
    ).toBeInTheDocument()
  })
})
