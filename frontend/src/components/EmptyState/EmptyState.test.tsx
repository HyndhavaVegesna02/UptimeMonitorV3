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
})
