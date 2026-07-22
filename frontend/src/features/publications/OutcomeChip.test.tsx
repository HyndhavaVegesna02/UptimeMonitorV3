import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { OutcomeChip } from './OutcomeChip'

describe('OutcomeChip', () => {
  it.each([
    ['succeeded', 'Succeeded'],
    ['failed', 'Failed'],
  ] as const)('renders a %s dot + visible text label (never colour alone)', (outcome, label) => {
    render(<OutcomeChip outcome={outcome} />)
    expect(screen.getByText(label)).toBeInTheDocument()
  })
})
