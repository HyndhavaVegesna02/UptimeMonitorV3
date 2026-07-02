import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Panel } from './Panel'

describe('Panel', () => {
  it('renders its children', () => {
    render(
      <Panel>
        <p>Panel content</p>
      </Panel>,
    )
    expect(screen.getByText('Panel content')).toBeInTheDocument()
  })

  it('renders an optional title as a heading', () => {
    render(<Panel title="Dashboard">content</Panel>)
    expect(
      screen.getByRole('heading', { name: 'Dashboard' }),
    ).toBeInTheDocument()
  })

  it('renders no heading when no title is given', () => {
    render(<Panel>content</Panel>)
    expect(screen.queryByRole('heading')).not.toBeInTheDocument()
  })

  it('applies the panel surface class', () => {
    const { container } = render(<Panel>content</Panel>)
    expect(container.querySelector('.panel')).not.toBeNull()
  })
})
