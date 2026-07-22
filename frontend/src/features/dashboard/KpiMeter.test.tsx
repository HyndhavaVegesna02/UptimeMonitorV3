import { render } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { KpiMeter } from './KpiMeter'

const kpiMeterCss = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), 'KpiMeter.css'), 'utf-8')

describe('KpiMeter', () => {
  it('fills proportionally to ratio', () => {
    const { container } = render(<KpiMeter ratio={0.25} tone="accent" />)
    const fill = container.querySelector('.kpi-meter__fill') as HTMLElement
    expect(fill.style.width).toBe('25%')
  })

  it('clamps a ratio above 1 to a solid flat bar', () => {
    const { container } = render(<KpiMeter ratio={4} tone="positive" />)
    const fill = container.querySelector('.kpi-meter__fill') as HTMLElement
    expect(fill.style.width).toBe('100%')
  })

  it('clamps a negative ratio to empty', () => {
    const { container } = render(<KpiMeter ratio={-1} tone="negative" />)
    const fill = container.querySelector('.kpi-meter__fill') as HTMLElement
    expect(fill.style.width).toBe('0%')
  })

  it('applies the tone class tied to the meaning rule (AC4), never left toneless', () => {
    const { container } = render(<KpiMeter ratio={1} tone="negative" />)
    expect(container.querySelector('.kpi-meter__fill--negative')).toBeInTheDocument()
  })

  it('is decorative — the KPI number/sub-line already carry the meaning', () => {
    const { container } = render(<KpiMeter ratio={1} tone="neutral" />)
    expect(container.querySelector('.kpi-meter')).toHaveAttribute('aria-hidden', 'true')
  })

  it('never uses transition: all (checklist: no blanket transitions)', () => {
    expect(kpiMeterCss).not.toMatch(/transition:\s*all\b/)
  })
})
