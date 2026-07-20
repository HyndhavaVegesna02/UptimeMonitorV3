import { CheckCircle, Warning } from '@phosphor-icons/react'
import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Icon } from './Icon'

describe('Icon', () => {
  it('renders decoratively (aria-hidden, no accessible name) when marked aria-hidden', () => {
    const { container } = render(<Icon icon={CheckCircle} aria-hidden />)
    const svg = container.querySelector('svg')
    expect(svg).not.toBeNull()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
    expect(svg).not.toHaveAttribute('role')
    expect(screen.queryByRole('img')).toBeNull()
  })

  it('exposes an accessible name via role="img" + aria-label when given a label', () => {
    render(<Icon icon={Warning} label="Degraded" />)
    expect(screen.getByRole('img', { name: 'Degraded' })).toBeInTheDocument()
  })

  it('defaults to the pinned size/weight and honors overrides', () => {
    const { container } = render(<Icon icon={CheckCircle} aria-hidden />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('width', '18')
    expect(svg).toHaveAttribute('height', '18')

    const { container: overridden } = render(
      <Icon icon={CheckCircle} aria-hidden size={24} weight="bold" />,
    )
    expect(overridden.querySelector('svg')).toHaveAttribute('width', '24')
  })
})
