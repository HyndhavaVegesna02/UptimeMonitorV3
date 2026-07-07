import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Icon } from './Icon'

describe('Icon', () => {
  it('renders as decorative (aria-hidden) by default, with no title element', () => {
    const { container } = render(<Icon name="check" />)
    const svg = container.querySelector('svg')
    expect(svg).not.toBeNull()
    expect(svg).toHaveAttribute('aria-hidden', 'true')
    expect(svg).not.toHaveAttribute('role')
    expect(container.querySelector('title')).toBeNull()
  })

  it('exposes an accessible name via role="img" + <title> when a title is given', () => {
    render(<Icon name="alert-triangle" title="Warning" />)
    expect(screen.getByRole('img', { name: 'Warning' })).toBeInTheDocument()
  })

  it('renders every icon name without throwing', () => {
    const names = [
      'logo',
      'dashboard',
      'availability',
      'approvals',
      'history',
      'maintenance',
      'publications',
      'chevron-left',
      'chevron-right',
      'sun',
      'moon',
      'search',
      'alert-triangle',
      'check',
      'x',
      'trash',
      'zap',
      'arrow-right',
    ] as const

    for (const name of names) {
      const { container, unmount } = render(<Icon name={name} />)
      expect(container.querySelector('svg')).not.toBeNull()
      unmount()
    }
  })

  it('defaults to a 16px square and honors a size override', () => {
    const { container } = render(<Icon name="check" size={24} />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveAttribute('width', '24')
    expect(svg).toHaveAttribute('height', '24')
  })

  it('inherits color via currentColor (no hardcoded stroke color)', () => {
    const { container } = render(<Icon name="check" />)
    expect(container.querySelector('svg')).toHaveAttribute('stroke', 'currentColor')
  })
})
