import { render, screen, within } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import type { ObservationDTO } from '../../api/types'
import { ResponseTimeChart } from './ResponseTimeChart'

const chartCss = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), 'ResponseTimeChart.css'),
  'utf-8',
)

const OBSERVATIONS: ObservationDTO[] = [
  { signal_key: 'http-check', observed_at: '2026-07-21T07:58:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000060', latency_ms: 588, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:57:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 951, response_status_code: 200, check_type: 'http' },
  { signal_key: 'http-check', observed_at: '2026-07-21T07:56:41Z', health: 'up', location: 'SYNTHETIC_LOCATION-0000000000000047', latency_ms: 293, response_status_code: 200, check_type: 'http' },
]

describe('ResponseTimeChart', () => {
  it('renders an SVG with role="img" and a descriptive aria-label', () => {
    render(<ResponseTimeChart observations={OBSERVATIONS} windowLabel="last 24 hours" />)
    const chart = screen.getByRole('img', { name: /Response time over the last 24 hours/ })
    expect(chart.tagName).toBe('svg')
  })

  it('renders axis gridline labels', () => {
    render(<ResponseTimeChart observations={OBSERVATIONS} windowLabel="last 24 hours" />)
    expect(screen.getAllByText(/ms$/).length).toBeGreaterThan(0)
  })

  it('renders a legend calling out the spike location and value', () => {
    const { container } = render(<ResponseTimeChart observations={OBSERVATIONS} windowLabel="last 24 hours" />)
    const legend = container.querySelector('.response-time-chart__legend')!
    expect(within(legend as HTMLElement).getByText(/951/)).toBeInTheDocument()
    expect(within(legend as HTMLElement).getByText(/0047/)).toBeInTheDocument()
  })

  it('renders an EmptyState when there is no history for the window', () => {
    render(<ResponseTimeChart observations={[]} windowLabel="last 24 hours" />)
    expect(screen.queryByRole('img')).toBeNull()
    expect(screen.getByText(/No response-time data/)).toBeInTheDocument()
  })

  it('marks the spike with a shape marker, not colour alone (a distinct circle element with a stroke)', () => {
    const { container } = render(<ResponseTimeChart observations={OBSERVATIONS} windowLabel="last 24 hours" />)
    expect(container.querySelector('circle')).not.toBeNull()
  })

  it('declares a one-shot entrance guarded by prefers-reduced-motion, animating only transform/opacity (AC2)', () => {
    expect(chartCss).toMatch(/@media \(prefers-reduced-motion: no-preference\)/)
    expect(chartCss).not.toMatch(/transition:\s*all\b/)
    expect(chartCss).toMatch(/animation:[^;]*response-time-chart-rise/)
  })
})
