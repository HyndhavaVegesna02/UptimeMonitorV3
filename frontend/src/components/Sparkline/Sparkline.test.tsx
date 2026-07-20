import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Sparkline } from './Sparkline'

const sparklineCss = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), 'Sparkline.css'),
  'utf-8',
)

describe('Sparkline', () => {
  it('renders an svg polyline through the given data points', () => {
    const { container } = render(<Sparkline data={[1, 2, 3, 2, 4]} />)
    const svg = container.querySelector('svg')
    expect(svg).not.toBeNull()
    const polyline = container.querySelector('polyline')
    expect(polyline).not.toBeNull()
    // 5 points -> 5 "x,y" pairs
    expect(polyline!.getAttribute('points')!.trim().split(' ')).toHaveLength(5)
  })

  it('is purely decorative by default (aria-hidden, no accessible name)', () => {
    const { container } = render(<Sparkline data={[1, 2, 3]} />)
    expect(container.querySelector('svg')).toHaveAttribute('aria-hidden', 'true')
  })

  it('renders a flat horizontal line when every value is equal (no NaN/division-by-zero)', () => {
    const { container } = render(<Sparkline data={[5, 5, 5, 5]} />)
    const points = container.querySelector('polyline')!.getAttribute('points')!
    expect(points).not.toMatch(/NaN/)
  })

  it('renders nothing (no crash) for an empty data array', () => {
    const { container } = render(<Sparkline data={[]} />)
    expect(container.querySelector('svg')).not.toBeNull()
    expect(container.querySelector('polyline')).toBeNull()
  })

  it('applies a tone class that maps to a semantic stroke token', () => {
    const { container } = render(<Sparkline data={[1, 2, 3]} tone="positive" />)
    expect(container.querySelector('svg')).toHaveClass('sparkline--positive')
  })

  it('the entrance animation is guarded by prefers-reduced-motion and animates only transform/opacity (AC5)', () => {
    expect(sparklineCss).toMatch(/@media \(prefers-reduced-motion: no-preference\)/)
    expect(sparklineCss).toMatch(/opacity/)
    // AC5 is explicit and unqualified: motion animates ONLY transform/opacity —
    // stroke-dashoffset (however paint-only) is not one of those two properties.
    expect(sparklineCss).not.toMatch(/stroke-dashoffset/)
    expect(sparklineCss).not.toMatch(/stroke-dasharray/)
  })
})
