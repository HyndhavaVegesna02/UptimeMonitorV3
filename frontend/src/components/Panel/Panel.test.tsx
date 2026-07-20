import { readFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Panel } from './Panel'

const panelCss = readFileSync(
  resolve(dirname(fileURLToPath(import.meta.url)), 'Panel.css'),
  'utf-8',
)

describe('Panel', () => {
  it('renders its children', () => {
    render(
      <Panel>
        <p>Body content</p>
      </Panel>,
    )
    expect(screen.getByText('Body content')).toBeInTheDocument()
  })

  it('renders an optional title as a level-2 heading by default', () => {
    render(<Panel title="Response time" />)
    expect(screen.getByRole('heading', { name: 'Response time', level: 2 })).toBeInTheDocument()
  })

  it('honors an explicit heading level for the page-level panel', () => {
    render(<Panel title="Design system" headingLevel="h1" />)
    expect(screen.getByRole('heading', { name: 'Design system', level: 1 })).toBeInTheDocument()
  })

  it('applies the interactive (hover-lift) modifier class when requested', () => {
    const { container } = render(<Panel interactive>Card</Panel>)
    expect(container.firstElementChild).toHaveClass('panel--interactive')
  })

  it('does not apply the interactive modifier by default', () => {
    const { container } = render(<Panel>Card</Panel>)
    expect(container.firstElementChild).not.toHaveClass('panel--interactive')
  })

  it('gates the hover-lift transform to fine-pointer hover devices and reduced-motion', () => {
    expect(panelCss).toMatch(/@media \(hover: hover\) and \(pointer: fine\)/)
    expect(panelCss).not.toMatch(/transition:\s*all/)
  })
})
