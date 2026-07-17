import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('renders the given message', () => {
    render(<EmptyState message="No components yet" />)
    expect(screen.getByText('No components yet')).toBeInTheDocument()
  })

  it('renders optional supporting detail text', () => {
    render(
      <EmptyState
        message="No components yet"
        detail="Components appear here once seeded."
      />,
    )
    expect(
      screen.getByText('Components appear here once seeded.'),
    ).toBeInTheDocument()
  })

  it('renders no icon by default (STORY-097 AC3)', () => {
    const { container } = render(<EmptyState message="No components yet" />)
    expect(container.querySelector('.empty-state__icon')).not.toBeInTheDocument()
  })

  it('renders an optional decorative icon, defaulting to a neutral tone (STORY-097 AC3)', () => {
    const { container } = render(<EmptyState message="Queue clear" icon="check" />)
    const icon = container.querySelector('.empty-state__icon')
    expect(icon).toHaveAttribute('aria-hidden', 'true')
    expect(icon).toHaveClass('empty-state__icon--neutral')
  })

  it('applies the "positive" tone when explicitly given (STORY-097 AC3)', () => {
    const { container } = render(
      <EmptyState message="Queue clear" icon="check" tone="positive" />,
    )
    expect(container.querySelector('.empty-state__icon')).toHaveClass(
      'empty-state__icon--positive',
    )
  })
})
