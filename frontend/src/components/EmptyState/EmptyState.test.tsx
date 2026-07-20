import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { EmptyState } from './EmptyState'

describe('EmptyState', () => {
  it('renders the required message', () => {
    render(<EmptyState message="No components yet" />)
    expect(screen.getByText('No components yet')).toBeInTheDocument()
  })

  it('renders an optional detail line', () => {
    render(<EmptyState message="No components yet" detail="Add one to get started." />)
    expect(screen.getByText('Add one to get started.')).toBeInTheDocument()
  })

  it('omits the detail line when not given', () => {
    const { container } = render(<EmptyState message="No components yet" />)
    expect(container.querySelector('.empty-state__detail')).toBeNull()
  })
})
