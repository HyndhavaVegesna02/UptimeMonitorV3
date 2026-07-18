import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LatencySpark } from './LatencySpark'

describe('LatencySpark', () => {
  it('renders an explicit "No data" state instead of a fabricated line for an empty series', () => {
    render(<LatencySpark points={[]} label="Frontend latency" />)

    expect(screen.getByRole('img', { name: 'Frontend latency: no data' })).toBeInTheDocument()
    expect(screen.getByText('No data')).toBeInTheDocument()
  })

  it('renders an SVG polyline with one point per value and an aria-label carrying the latest value', () => {
    render(<LatencySpark points={[100, 250, 180]} label="Frontend latency" />)

    const svg = screen.getByRole('img', { name: 'Frontend latency: latest 180 ms' })
    expect(svg.tagName.toLowerCase()).toBe('svg')

    const polyline = svg.querySelector('polyline')!
    const coordinatePairs = polyline.getAttribute('points')!.trim().split(/\s+/)
    expect(coordinatePairs).toHaveLength(3)
  })

  it('carries an SVG <title> for assistive tech that reads titles rather than aria-label', () => {
    render(<LatencySpark points={[100, 250, 180]} label="Frontend latency" />)

    const svg = screen.getByRole('img', { name: 'Frontend latency: latest 180 ms' })
    expect(svg.querySelector('title')?.textContent).toBe('Frontend latency: latest 180 ms')
  })

  it('renders a flat line (no NaN) when every point shares the same value', () => {
    render(<LatencySpark points={[200, 200, 200]} label="Flat" />)

    const svg = screen.getByRole('img', { name: 'Flat: latest 200 ms' })
    const polyline = svg.querySelector('polyline')!
    expect(polyline.getAttribute('points')).not.toContain('NaN')
  })
})
