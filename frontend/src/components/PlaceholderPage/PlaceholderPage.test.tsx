import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PlaceholderPage } from './PlaceholderPage'

describe('PlaceholderPage', () => {
  it('renders the given description and a "coming soon" note, with no top-level heading', () => {
    render(<PlaceholderPage description="Per-component availability metrics." />)
    expect(screen.getByText('Per-component availability metrics.')).toBeInTheDocument()
    expect(screen.getByText('Coming soon.')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { level: 1 })).toBeNull()
  })
})
