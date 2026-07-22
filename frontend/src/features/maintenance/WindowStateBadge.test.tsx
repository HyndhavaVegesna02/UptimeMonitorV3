import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { WindowStateBadge } from './WindowStateBadge'

describe('WindowStateBadge', () => {
  it.each([
    ['upcoming', 'Upcoming'],
    ['active', 'Active'],
    ['past', 'Past'],
  ] as const)('renders a %s dot + visible text label (never colour alone)', (state, label) => {
    render(<WindowStateBadge state={state} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })
})
